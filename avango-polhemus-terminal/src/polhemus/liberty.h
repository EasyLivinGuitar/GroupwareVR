
#ifndef _LIBERTY_H
#define _LIBERTY_H

#include "PiTracker.h"
#include "PingPong.h"
#include "PiTerm.h"

#include <string>



struct pose_t {
	unsigned short 	id;
	float			pose[6];
};


// --------------------------------------------------------------------------
// Liberty class (quick&dirty-hack to enscapulate connection dependend data)

class Liberty
{
  public:

	Liberty();
	~Liberty();

	// --------------------------------------------------------------------------
	// Initialize Lib
	
	// Initialization:
	// ini (i): parameters
	// return value (o): error code

	int init(void);
	
	// Exit:
	// return value (o): error code

	int exit(void);

	static void* ReadTrackerThread( void* pParam );
    int receiveData(unsigned int* nmarker, pose_t* pose, int max_nmarker);
	
  protected:

  private:
 	void connect(LPCNX_STRUCT pcs);
	int split_lines(char* str, unsigned long len, char** strarr, int maxlines);
	void disconnect(LPCNX_STRUCT pcs);
	bool sendCommand(std::string cmd, LPCNX_STRUCT pcs );
	int sendInitialCommands();

  private:
	 LPREAD_WRITE_STRUCT mReadStruct_;
	 LPREAD_WRITE_STRUCT mWriteStruct_;
	 PingPong			 mPong_;
	 CNX_STRUCT			 mcnxStruct_;
	 CNX_PARAMS			 mcp_;
	 pthread_t			 mthread_id_;
};



#endif // _LIBERTY_H
