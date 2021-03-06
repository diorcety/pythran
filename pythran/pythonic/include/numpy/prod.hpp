#ifndef PYTHONIC_INCLUDE_NUMPY_PROD_HPP
#define PYTHONIC_INCLUDE_NUMPY_PROD_HPP

#include "pythonic/include/utils/functor.hpp"
#include "pythonic/include/numpy/reduce.hpp"
#include "pythonic/include/operator_/imul.hpp"

namespace pythonic
{

  namespace numpy
  {

    template <class... Args>
    auto prod(Args &&... args) -> decltype(
        reduce<operator_::functor::imul>(std::forward<Args>(args)...));

    DECLARE_FUNCTOR(pythonic::numpy, prod);
  }
}

#endif
