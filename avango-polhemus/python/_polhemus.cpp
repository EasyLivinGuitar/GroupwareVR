// -*- Mode:C++ -*-

/************************************************************************\
*                                                                        *
* This file is part of Avango.                                           *
*                                                                        *
* Copyright 1997 - 2008 Fraunhofer-Gesellschaft zur Foerderung der       *
* angewandten Forschung (FhG), Munich, Germany.                          *
*                                                                        *
* Avango is free software: you can redistribute it and/or modify         *
* it under the terms of the GNU Lesser General Public License as         *
* published by the Free Software Foundation, version 3.                  *
*                                                                        *
* Avango is distributed in the hope that it will be useful,              *
* but WITHOUT ANY WARRANTY; without even the implied warranty of         *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the           *
* GNU General Public License for more details.                           *
*                                                                        *
* You should have received a copy of the GNU Lesser General Public       *
* License along with Avango. If not, see <http://www.gnu.org/licenses/>. *
*                                                                        *
* Avango is a trademark owned by FhG.                                    *
*                                                                        *
\************************************************************************/

#include <avango/Type.h>
#include <avango/Link.h>
#include <avango/daemon/polhemus/Polhemus.h>
#include <boost/python.hpp>

using namespace boost::python;

namespace boost {
  namespace python {
    template <class T> struct pointee<av::Link<T> > {
      typedef T type;
    };
  }
}

BOOST_PYTHON_MODULE(_polhemus)
{
  av::daemon::polhemus::Polhemus::initClass();
  // Avango BOOST_PYTHON_MODULE(_polhemus)

  class_<av::daemon::polhemus::Polhemus,
         av::Link<av::daemon::polhemus::Polhemus>,
         bases<av::daemon::Device>,
         boost::noncopyable>(
      "_PolhemusHelper",
      "A helper class that provides some basic properties and function "
      "inherited from Polhemus,"
      "used to construct a concrete Python device representation.");
}
