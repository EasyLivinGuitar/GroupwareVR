#include "liberty.h"
//#include <stdio.h>
//#include <unistd.h>
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

// --------------------------------------------------------------------------
// Constructor & Destructor

Liberty::Liberty()
: mReadStruct_(), mWriteStruct_(), mPong_(), mcnxStruct_(), mcp_(), mthread_id_()
{

}

Liberty::~Liberty() {
	if(mcnxStruct_.pTrak) {
		delete mcnxStruct_.pTrak;
	}
}


// --------------------------------------------------------------------------
// Initialization:
// ini (i): parameters
// return value (o): error code

int Liberty::init() {	
	if(mPong_.InitPingPong(BUFFER_SIZE) < 0) {
		// throw error that memalloc failed
		std::cerr << "Memory Allocation Error setting up buffers!" << std::endl;
		return( -1 );
	}

	//const int keepLooping = 0;
	int* keepLooping = new int;
	*keepLooping = 0;

	// set up USB connection
	mcnxStruct_.cnxType = USB_CNX;
	mcnxStruct_.trackerType = TRKR_LIB_HS;//connect with high speed libertiy latus
	//std::strncpy(mcp_.port, "/dev/ttyS0", 50);

	mcnxStruct_.pTrak = new PiTracker;

	if( !mcnxStruct_.pTrak ) {
		// throw error 
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

	connect();


	if( sendInitialCommands() < 0 )	{
		std::cout << "FATAL ERROR: sending initial commands to tracker" << std::endl;
		return -1;
	}

	*(mReadStruct_->keepLooping) = 1;
	
	pthread_create( mReadStruct_->pthread,
		NULL,
		ReadTrackerThread,
		mReadStruct_
	);
	
	return 0;
}

int Liberty::sendInitialCommands() {
	std::cout << "Please wait..." << std::endl;

	// usleep(2000000); // 3s
	// std::cout << "Calibrating for first receiver" << std::endl;

	// if(!sendCommand("a1\r")) {
	// 	return -1;		
	// }

	std::cout << "Switch: autodetect markers" << std::endl;
	usleep(1000000);
	if(!sendCommand("@A1\r"))	{
		return -2;
	}


	std::cout << "Switch: metric units" << std::endl;
	usleep(1000000);
	if(!sendCommand("U1\r"))	{
		return -3;
	}
	
	std::cout << "Switch: continous read stream" << std::endl;
	// wait a second ;)
	// good ole machine needs time 
	usleep(1000000);
	if(!sendCommand("c\r"))	{
		return -4;
	}

	return 0;
}

void Liberty::connect() {
	int cnxSuccess;
	//char* str;
	//char* port;

	if(mcnxStruct_.cnxType == USB_CNX)	{
		do {

			std::cout << "attempting UsbConnect("
				<< usbTrkParams[mcnxStruct_.trackerType].vid
				<< "," << usbTrkParams[mcnxStruct_.trackerType].pid
				<< "," << usbTrkParams[mcnxStruct_.trackerType].writeEp
				<< "," << usbTrkParams[mcnxStruct_.trackerType].readEp
				<<")..." << std::endl;

			//try to connect
			cnxSuccess = mcnxStruct_.pTrak->UsbConnect(
				usbTrkParams[mcnxStruct_.trackerType].vid,
				usbTrkParams[mcnxStruct_.trackerType].pid,
				usbTrkParams[mcnxStruct_.trackerType].writeEp,
				usbTrkParams[mcnxStruct_.trackerType].readEp
			);

			if( cnxSuccess != 0 ) {		
				std::cerr << "UsbConnect() failed..." << std::endl;
			}
		} while( false);
	}

	std::cout << "Connected to " << trackerNames[mcnxStruct_.trackerType] << " over USB" << std::endl;
	
	
	// start read thread

	LPREAD_WRITE_STRUCT prs = mReadStruct_;
	*(prs->keepLooping) = 1;
	
	pthread_create( prs->pthread, NULL, ReadTrackerThread, prs);
	
}


void Liberty::disconnect() {
	LPREAD_WRITE_STRUCT prs = mReadStruct_;
	prs->keepLooping = 0;
	pthread_join( *prs->pthread, NULL); // wait for read thread
	mcnxStruct_.pTrak->CloseTrk(); // close tracker connection
}


/* static */ void* Liberty::ReadTrackerThread( void* pParam ) {
	BYTE buf[BUFFER_SIZE];
  LPREAD_WRITE_STRUCT prs=(LPREAD_WRITE_STRUCT)pParam;
  PiTracker* pTrak=(PiTracker*)prs->pParam;
  int len=0;
  int bw;

  // first establish comm and clear out any residual trash data
  do {
    pTrak->WriteTrkData((void*)"\r",1);  // send just a cr, should return an short "Invalid Command" response
    usleep(100000);
    len=pTrak->ReadTrkData(buf,BUFFER_SIZE);  // keep trying till we get a response
  } while (!len);


  while (prs->keepLooping){

    len=pTrak->ReadTrkData(buf,BUFFER_SIZE);  // read tracker data
    if (len>0 && len<BUFFER_SIZE){
      buf[len]=0;  // null terminate
      do {
		bw=prs->pPong->WritePP(buf,len);  // write to buffer
		usleep(1000);
      } while(!bw);
    }
    usleep(2000);  // rest for 2ms
  }

  return NULL;
}

bool Liberty::sendCommand(std::string cmd) {
	if( mcnxStruct_.pTrak->GetCnxType() == NO_CNX )	{
		std::cout << "FATAL ERROR! Connection to tracker lost!" << std::endl;
		return( false );
	}
	std::cout << "sending command: "<< cmd << std::endl;
	mcnxStruct_.pTrak->WriteTrkData( const_cast<char*>( cmd.c_str() ), cmd.length() );
	return( true );
}


int Liberty::receiveData(unsigned int* nmarker, pose_t* pose, int max_nmarker) {
	// Defaults:
	*nmarker = 0;
	
	// send command to receive snapshot
	//sendCommand("p");
	//usleep(2000);

	LPREAD_WRITE_STRUCT lws = mWriteStruct_;
	BYTE buf[BUFFER_SIZE];
	std::string s;

	int len = lws->pPong->ReadPP(buf);

	while(len) 	{
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

		for(tokenizer::iterator tok_iter = tokens.begin(); tok_iter != tokens.end(); ++tok_iter, ++c) {
			// marker data is always 7 valus 
			if(c % 7 == 0) {// guess it's an Id value
				try	{
					id = lexical_cast<unsigned short>(*tok_iter);
					if(id > 0 && id <= max_nmarker)	{
						pose[id - 1].id = id;
						// std::cout << "Catched ID: " << id << std::endl;
						*nmarker = std::max(*nmarker, id);
						//std::cout << "setting nmarker to " << *nmarker << std::endl;
					}
				}
				catch(bad_lexical_cast &)	{
					id = 0;
				}
			}
			else if( id > 0 && id <= max_nmarker){
				try	{
					float val = lexical_cast<float>(*tok_iter);
					pose[id - 1].pose[ c % 7 - 1 ] = val;
					//std::cout << "Catched Value: " << val << std::endl;
				}
				catch(bad_lexical_cast &) {

				}
			}
		}

		len = lws->pPong->ReadPP(buf);
	}

	return len;
}

std::string Liberty::readString() {

	BYTE buf[BUFFER_SIZE];
	std::string s;

	int len = mWriteStruct_->pPong->ReadPP(buf);
	while(len) 	{
		buf[len] = 0; // never forget null termination DOH
		std::string s;
		s.assign((char*)buf);
		len = mWriteStruct_->pPong->ReadPP(buf);
	}
	return s;
}


int Liberty::split_lines(char* str, unsigned long len, char** strarr, int maxlines) {
	unsigned long i = 0;
	int index = 0;
	char* s = str;

	while(*str && (i<len)){
		if(*str == '\r') {         // substitute cr
			*str = '\0';
		} else if(*str == '\n') {   // lf: end of line found
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

int Liberty::exit(void) {
	disconnect();
	
	return 0;
}


