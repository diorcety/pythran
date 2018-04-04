#ifndef PYTHONIC_INCLUDE_PAST_BUILTINS_XRANGE_HPP
#define PYTHONIC_INCLUDE_PAST_BUILTINS_XRANGE_HPP

#include "pythonic/include/__builtin__/xrange.hpp"

PYTHONIC_NS_BEGIN
namespace past
{

  namespace builtins
  {
    using xrange = __builtin__::xrange;

    namespace functor = __builtin__::functor;
  }

}
PYTHONIC_NS_END

#endif
