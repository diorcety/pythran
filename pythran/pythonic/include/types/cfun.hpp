#ifndef PYTHONIC_INCLUDE_TYPES_CFUN_HPP
#define PYTHONIC_INCLUDE_TYPES_CFUN_HPP

namespace pythonic
{

  namespace types
  {

    template <class T>
    struct cfun;

    template <class ReturnType, class... ArgsType>
    struct cfun<ReturnType(ArgsType...)> {

      using callable = void;

      cfun(ReturnType (*fun)(ArgsType...));

      ReturnType (*ptr)(ArgsType...);

      ReturnType operator()(ArgsType... args) const;
    };
  }
}

#ifdef ENABLE_PYTHON_MODULE

#include "pythonic/python/core.hpp"

namespace pythonic
{

  template <class R, class... Args>
  struct to_python<types::cfun<R(Args...)>> {
    static PyObject *convert(types::cfun<R(Args...)> const &v);
  };

  template <class R, class... Args>
  struct from_python<types::cfun<R(Args...)>> {
    static bool is_convertible(PyObject *obj);
    static types::cfun<R(Args...)> convert(PyObject *obj);
  };
}

#endif

#endif
