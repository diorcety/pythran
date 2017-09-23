#ifndef PYTHONIC_INCLUDE_NUMPY_SUM_HPP
#define PYTHONIC_INCLUDE_NUMPY_SUM_HPP

#include "pythonic/include/numpy/reduce.hpp"
#include "pythonic/include/operator_/iadd.hpp"
#include "pythonic/include/utils/functor.hpp"

namespace pythonic
{

  namespace numpy
  {

    template <class... Args>
    auto sum(Args &&... args) -> decltype(
        reduce<operator_::functor::iadd>(std::forward<Args>(args)...));

    DECLARE_FUNCTOR(pythonic::numpy, sum);
  }
}

#endif
