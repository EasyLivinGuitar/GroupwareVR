#include "polhemus/liberty.h"
#include <errno.h>
#include <scm/core/math.h>
#include <gua/math.hpp>
#include <avango/Logger.h>
#include <avango/daemon/polhemus/Polhemus.h>
#include <avango/daemon/Station.h>
#include <cstring>
#include <string>

namespace
{
  av::Logger& logger(av::getLogger("av::daemon::polhemus::Polhemus"));
}

AV_BASE_DEFINE(av::daemon::polhemus::Polhemus);

av::daemon::polhemus::Polhemus::Polhemus()
  : mPolhemus(new ::Liberty)
{}

av::daemon::polhemus::Polhemus::~Polhemus()
{}

void av::daemon::polhemus::Polhemus::initClass()
{
  if (!isTypeInitialized()) {
    av::daemon::Device::initClass();
    AV_BASE_INIT(av::daemon::Device, av::daemon::polhemus::Polhemus, true);
  }
}

void av::daemon::polhemus::Polhemus::startDevice()
{
  logger.info() << "startDevice: device configured successfully";

  // TODO
  // initialize
  mPolhemus->init();

  logger.info() << "startDevice: device initialized successfully";
}

void av::daemon::polhemus::Polhemus::readLoop()
{
  // DEBUG!!!
  //return;

  //std::cout << "DEBUG: readLoop() called..." << std::endl;
  logger.info() << "entering readLoop()";

  unsigned int max_marker = 0;
  unsigned int max_station_id = 1;
  pose_t* buf = 0;

  unsigned int nmarker;

  while (mKeepRunning) {

    for (auto current = mStations.begin(); current != mStations.end();
         ++current) {
      if (static_cast<unsigned>((*current).first) > max_station_id) {
        max_station_id = (*current).first;
      }
    }

    if (max_marker < max_station_id) {
      if (buf)
        ::free(buf);

      max_marker = max_station_id;
      buf = (pose_t*)::malloc(sizeof(pose_t) * max_marker);
    }

    // fetch pose from Liberty object
    mPolhemus->receiveData(&nmarker, buf, max_marker);

    if (/* error */ false) {
      // TODO some error handling if data is malformed
      // ? has not yet happened yet.
      // if the marker is not reachable - no data is sent or last pose will be
      // used
    } else {
      unsigned int marker_limit =
          std::min(static_cast<unsigned>(nmarker), max_marker);
      //std::cout << "Marker limit: " << marker_limit << std::endl;
      //std::cout << "nmarker: " << nmarker << std::endl;
      //std::cout << "max_marker: " << max_marker << std::endl;

      marker_limit = max_marker;

      for (unsigned int i = 0; i < marker_limit; ++i) {

        const int marker_idx = buf[i].id;
        NumStationMap::iterator it = mStations.find(marker_idx);

        if (it != mStations.end()) {
          //logger.info() << "readLoop: detected marker with ID = %s",
          //buf[i].id;
          // form transformation matrix
          double deg2rad = 0.0175;
          double yaw_a = buf[i].pose[3] * deg2rad;
          double pitch_a = buf[i].pose[4] * deg2rad;
          double roll_a = buf[i].pose[5] * deg2rad;

          (*it).second->setValue(0, buf[i].pose[3]);
          (*it).second->setValue(1, buf[i].pose[4]);
          (*it).second->setValue(2, buf[i].pose[5]);
          logger.debug() << "readLoop: set value 0,1,2 of station number '%s'",
              marker_idx;

#if 0
          rot.makeRotate(yaw_a,
                         ::gua::math::vec3f(1.0f, 0.0f, 0.0f),
                         pitch_a,
                         ::gua::math::vec3f(0.0f, 1.0f, 0.0f),
                         roll_a,
                         ::gua::math::vec3f(0.0f, 0.0f, 1.0f));

#endif
          ::gua::math::mat4 rot = ::scm::math::make_rotation(yaw_a, pitch_a, roll_a, 0.0);
          ::gua::math::mat4 trans = ::scm::math::make_translation(::gua::math::vec3(
                              buf[i].pose[0] * 0.1,
                              buf[i].pose[1] * 0.1,
                              buf[i].pose[2] * 0.1));

          ::gua::math::mat4 xform = rot * trans;

          (*it).second->setMatrix(xform);
          logger.debug() << "readLoop: set matrix of station number '%s'",
              marker_idx;
          // std::cout << "Id: " << i << std::endl;
          // std::cout << "Translation: " << buf[i].pose[0] << " " <<
          // buf[i].pose[1] << " " << buf[i].pose[2] << std::endl;
        } else {
          logger.debug() << "readLoop: can't find station for body #%d "
                            "(station not configured?)",
              marker_idx;
        }
      }
    }
  }
}

void av::daemon::polhemus::Polhemus::stopDevice()
{
  mPolhemus->exit();
  logger.info() << "stopDevice: done.";
}

std::vector<std::string> const &
av::daemon::polhemus::Polhemus::queryFeatures()
{
  return mRequiredFeatures;
}
