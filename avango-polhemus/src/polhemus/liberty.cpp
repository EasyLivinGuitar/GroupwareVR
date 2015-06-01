#include "liberty.h"
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include "PiTracker.h"
#include "PingPong.h"
#include "PiTerm.h"
#include <iostream>
#include <cstring>
#include <string>

#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>

#define BUFFER_SIZE     1000

namespace {

// usb vid/pids for Polehemus trackers
USB_PARAMS usbTrkParams[NUM_SUPP_TRKS]={
  {0x0f44,0xff20,0x04,0x88},  // Lib HS
  {0x0f44,0xff12,0x02,0x82},   // Lib
  {0x0f44,0xef12,0x02,0x82},  // Patriot
  {0x0f44,0x0002,0x02,0x82}};  // Fastrak

// polhemus tracker names
const char* trackerNames[NUM_SUPP_TRKS]={
  "High Speed Liberty","Liberty","Patriot","Fastrak"};


}



// --------------------------------------------------------------------------
// Constructor & Destructor

Liberty::Liberty()
: mReadStruct_(), mWriteStruct_(), mPong_(), mcnxStruct_(), mcp_(), mthread_id_()
{
}

Liberty::~Liberty()
{
	if(mcnxStruct_.pTrak)
	{
		delete mcnxStruct_.pTrak;
	}
}


// --------------------------------------------------------------------------
// Initialization:
// ini (i): parameters
// return value (o): error code

int Liberty::init()
{	
	if(mPong_.InitPingPong(BUFFER_SIZE) < 0)
	{
		// throw error that memalloc failed
		// fprintf(stderr, "Memory Allocation Error setting up buffers!\n");
		std::cerr << "Memory Allocation Error setting up buffers!" << std::endl;
		return( -1 );
	}

	//const int keepLooping = 0;
	int* keepLooping = new int;
	*keepLooping = 0;

	// set up USB connection
	mcnxStruct_.cnxType = USB_CNX;
	mcnxStruct_.trackerType = TRKR_LIB_HS;
	//std::strncpy(mcp_.port, "/dev/ttyS0", 50);

	mcnxStruct_.pTrak = new PiTracker;

	if( !mcnxStruct_.pTrak )
	{
		// throw error 
		// fprintf(stderr, "Memory Allocation Error creating tracker communication module!\n");
		std::cerr << "Memory Allocation Error creating tracker communication module!" << std::endl;
		return( -3 );
	}

	// set up read_write structs to read data in worker thread
	//READ_WRITE_STRUCT readStruct = {&mpong_, keepLooping, &mthread_id_, mcnxStruct_.pTrak };
	//READ_WRITE_STRUCT writeStruct = {&mpong_, keepLooping, &mthread_id, NULL);

	mReadStruct_ = new READ_WRITE_STRUCT;
	mReadStruct_->pPong = &mPong_;
	mReadStruct_->keepLooping = keepLooping;
	mReadStruct_->pthread = &mthread_id_;
	mReadStruct_->pParam = mcnxStruct_.pTrak;

	mWriteStruct_ = new READ_WRITE_STRUCT;
	mWriteStruct_->pPong = &mPong_;
	mWriteStruct_->keepLooping = keepLooping;
	mWriteStruct_->pthread = &mthread_id_;
	mWriteStruct_->pParam = NULL;

	connect(&mcnxStruct_);

	
/*

	usleep(10000);
	sendCommand("a1\r", &mcnxStruct_); // calibrate for first receiver
	usleep(10000);
	sendCommand("@A1\r", &mcnxStruct_); // autodetect markers

*/
	
	

	if( sendInitialCommands() < 0 )
	{
		std::cout << "FATAL ERROR: sending initial commands to tracker" << std::endl;
		return -1;
	}

	LPREAD_WRITE_STRUCT prs = mReadStruct_;
	*(prs->keepLooping) = 1;
	
	pthread_create( prs->pthread, NULL, ReadTrackerThread, prs);
	
	return 0;
}

int
Liberty::sendInitialCommands()
{
	std::cout << "Please wait..." << std::endl;

	usleep(1000000); // 3s
	std::cout << "Calibrating for first receiver" << std::endl;

	if(!sendCommand("a1\r", &mcnxStruct_))
	{
		return -1;		
	}

	std::cout << "Switch: autodetect markers" << std::endl;
	usleep(1000000);
	if(!sendCommand("@A1\r", &mcnxStruct_))
	{
		return -2;
	}


	std::cout << "Switch: metric units" << std::endl;
	usleep(1000000);
	if(!sendCommand("U1\r", &mcnxStruct_))
	{
		return -3;
	}
	
	std::cout << "Switch: continous read stream" << std::endl;
	// wait a second ;)
	// good ole machine needs time 
	usleep(1000000);
	if(!sendCommand("c\r", &mcnxStruct_))
	{
		return -4;
	}

	return 0;
}

void
Liberty::connect(LPCNX_STRUCT pcs)
{
	int cnxSuccess;
	//char* str;
	//char* port;

	if(pcs->cnxType == USB_CNX)
	{
		do {
			std::cout << "attempting UsbConnect()..." << std::endl;
			cnxSuccess=pcs->pTrak->UsbConnect(usbTrkParams[pcs->trackerType].vid, usbTrkParams[pcs->trackerType].pid, usbTrkParams[pcs->trackerType].writeEp, usbTrkParams[pcs->trackerType].readEp );
//			cnxSuccess=pcs->pTrak->UsbConnect(3908, 65312, 4, 136); // magic values for debugging purpose

			if( cnxSuccess != 0 )
			{		
				// throw failure message
				std::cerr << "UsbConnect() failed..." << std::endl;
			}
		} while( cnxSuccess != 0 );
	}

	std::cout << "Connected to " << trackerNames[pcs->trackerType] << " over USB" << std::endl;
	
	/*
	// start read thread

	LPREAD_WRITE_STRUCT prs = mReadStruct_;
	*(prs->keepLooping) = 1;
	
	pthread_create( prs->pthread, NULL, ReadTrackerThread, prs);
	*/
}


void
Liberty::disconnect(LPCNX_STRUCT pcs)
{
	LPREAD_WRITE_STRUCT prs = mReadStruct_;
	prs->keepLooping = 0;
	pthread_join( *prs->pthread, NULL); // wait for read thread
	pcs->pTrak->CloseTrk(); // close tracker connection
}


/* static */ void*
Liberty::ReadTrackerThread( void* pParam )
{
	BYTE buf[BUFFER_SIZE];
	LPREAD_WRITE_STRUCT prs = (LPREAD_WRITE_STRUCT)pParam;
	PiTracker* pTrak = (PiTracker*)prs->pParam;

	int len = 0;
	int bw;

	// establish comm and clear out residual trash data
	do {
		pTrak->WriteTrkData( (void*)"\r", 1); // send a cr - should return "invalid command"
		usleep(100000);
		len = pTrak->ReadTrkData(buf, BUFFER_SIZE); // keep trying till we get a response
	} while( !len );

	while( prs->keepLooping )
	{
		len = pTrak->ReadTrkData( buf, BUFFER_SIZE ); // read tracker data
		if( len > 0 && len < BUFFER_SIZE )
		{
			buf[len] = 0; // null terminate
			do {
				bw = prs->pPong->WritePP( buf, len ); // write to buffer
				usleep(1000);
			} while( !bw );
			usleep(2000); // rest for 2 ms
		}
	}
// 
	return NULL;
}

bool
Liberty::sendCommand(std::string cmd, LPCNX_STRUCT pcs)
{
	if( pcs->pTrak->GetCnxType() == NO_CNX )
	{
		std::cout << "FATAL ERROR! Connection to tracker lost!" << std::endl;
		return( false );
	}
	
	pcs->pTrak->WriteTrkData( const_cast<char*>( cmd.c_str() ), cmd.length() );

	return( true );
}


int
Liberty::receiveData(unsigned int* nmarker, pose_t* pose, int max_nmarker)
{
	// Defaults:
	*nmarker = 0;
	
	// send command to receive snapshot
	//sendCommand("p", &mcnxStruct_);
	//usleep(2000);

	LPREAD_WRITE_STRUCT lws = mWriteStruct_;
	BYTE buf[BUFFER_SIZE];
	std::string s;

	int len = lws->pPong->ReadPP(buf);

	while(len) 
	{
		using namespace boost;

		buf[len] = 0; // never forget null termination DOH
		
		s.assign((char*)buf);
		// process in this read cycle with tokenizer
		//std::cout << "String: " << s << std::endl;	
	
		typedef boost::tokenizer<boost::char_separator<char> > tokenizer;
		boost::char_separator<char> sep(" \t\n\r");
		tokenizer tokens(s, sep);

		unsigned int c(0);
		unsigned int id(0);

		for(tokenizer::iterator tok_iter = tokens.begin(); tok_iter != tokens.end(); ++tok_iter, ++c)
		{
			// marker data is always 7 valus 
			if(c % 7 == 0) // guess it's an Id value
			{
				try
				{
					id = lexical_cast<unsigned short>(*tok_iter);
					if(id > 0 && id <= max_nmarker)
					{
						pose[id - 1].id = id;
						// std::cout << "Catched ID: " << id << std::endl;
						*nmarker = std::max(*nmarker, id);
						//std::cout << "setting nmarker to " << *nmarker << std::endl;
					}
				}
				catch(bad_lexical_cast &)
				{
					id = 0;
				}
			}
			else if( id > 0 && id <= max_nmarker)
			{
				try
				{
					float val = lexical_cast<float>(*tok_iter);
					pose[id - 1].pose[ c % 7 - 1 ] = val;
					//std::cout << "Catched Value: " << val << std::endl;
				}
				catch(bad_lexical_cast &)
				{

				}
			}
		}

		len = lws->pPong->ReadPP(buf);
	}

	return len;
}


int Liberty::split_lines(char* str, unsigned long len, char** strarr, int maxlines)
{
	unsigned long i = 0;
	int index = 0;
	char* s = str;

	while(*str && (i<len)){
		if(*str == '\r'){         // substitute cr
			*str = '\0';
		}else if(*str == '\n'){   // lf: end of line found
			*str = '\0';
			
			strarr[index++] = s;
			if(index == maxlines){  // stop processing, if maximum number reached
				return index;
			}
			s = str + 1;
		}
		str++;
		i++;
	}

	return index;
}

// --------------------------------------------------------------------------
// Exit:
// return value (o): error code

int Liberty::exit(void)
{
	disconnect(&mcnxStruct_);
	
	return 0;
}


