#if !defined(AV_DAEMON_POLHEMUS_H)
#define AV_DAEMON_POLHEMUS_H

#include <avango/daemon/Device.h>

/**
 * \file
 * \ingroup av_daemon
 */

/**
 * Foreward declaration of the Polhemus class declarated in polhemus.h
 */
class Liberty;

namespace av {
namespace daemon {
namespace polhemus {
/**
	     * \ingroup av_daemon
	     */
class Polhemus : public Device {
  AV_BASE_DECLARE();

 public:
  /**
	       * Constructor
	       */
  Polhemus();

 protected:

  /**
	       * Destructor made protected to prevent allocation on stack.
	       */
  virtual ~Polhemus();

  /**
	       * Inherited from base class, implements the initialization of this
device.
	       */
  void startDevice();

  /**
	       * Inherited from base class, implements the loop in which the device is
read out.
	       */
  void readLoop();

  /**
	       * Inherited from base class, implements the closing operation of this
device.
	       */
  void stopDevice();

  /**
	       * Inherited from base class, returns a list of settable features.
	       */
  const std::vector<std::string>& queryFeatures();

 private:

  ::std::vector< ::std::string> mRequiredFeatures;

  ::boost::shared_ptr< ::Liberty> mPolhemus;

};
}
}
}

#endif
