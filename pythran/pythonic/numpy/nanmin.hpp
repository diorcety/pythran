#ifndef PYTHONIC_NUMPY_NANMIN_HPP
#define PYTHONIC_NUMPY_NANMIN_HPP

#include "pythonic/include/numpy/nanmin.hpp"
#include "pythonic/include/numpy/nan.hpp"

#include "pythonic/utils/functor.hpp"
#include "pythonic/types/ndarray.hpp"
#include "pythonic/builtins/ValueError.hpp"
#include "pythonic/numpy/isnan.hpp"

PYTHONIC_NS_BEGIN

namespace numpy
{
  namespace
  {
    template <class E, class F>
    bool _nanmin(E begin, E end, F &min, utils::int_<1>)
    {
      bool found = false;
      for (; begin != end; ++begin) {
        auto curr = *begin;
        if (!functor::isnan()(curr) && curr <= min) {
          min = curr;
          found = true;
        }
      }
      return found;
    }

    template <class E, class F, size_t N>
    void _nanmin(E begin, E end, F &min, utils::int_<N>)
    {
      bool found = false;
      for (; begin != end; ++begin)
        found |= _nanmin((*begin).begin(), (*begin).end(), min, utils::int_<N - 1>());
      return found;
    }

    template <class E, class F, size_t N, typename = typename std::enable_if<
        !std::is_floating_point<typename std::decay<E>::type>::value,
        bool>::type>
    void _nanmin2(E begin, E end, F &min, utils::int_<N> n)
    {
      _nanmin(begin, end, min, n);
    }

    template <class E, class F, size_t N, typename = typename std::enable_if<
        std::is_floating_point<typename std::decay<E>::type>::value,
        bool>::type>
    void _nanmin2(E begin, E end, F &min, utils::int_<N>)
    {
      if(_nanmin(begin, end, min, n)) min = numpy::nan;
    }
  }

  template <class E>
  typename E::dtype nanmin(E const &expr)
  {
    typename E::dtype min = std::numeric_limits<typename E::dtype>::max();
    _nanmin(expr.begin(), expr.end(), min, utils::int_<E::value>());
    return min;
  }
}
PYTHONIC_NS_END

#endif
