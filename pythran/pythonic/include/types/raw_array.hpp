#ifndef PYTHONIC_INCLUDE_TYPES_RAW_ARRAY_HPP
#define PYTHONIC_INCLUDE_TYPES_RAW_ARRAY_HPP

#include <functional>

PYTHONIC_NS_BEGIN

namespace types
{
  enum class ownership {
    external,
    owned,
  };
  /* Wrapper class to store an array pointer
   *
   * for internal use only, meant to be stored in a shared_ptr
   */
  template <class T>
  class raw_array
  {
    raw_array(raw_array<T> const &) = delete;

  public:
    using pointer_type = T *;

    T *data;
    raw_array();
    raw_array(size_t n);
    raw_array(T *d, ownership o);
    raw_array(T *d, const std::function<void(pointer_type)> &fct);
    raw_array(raw_array<T> &&d);
    void forget();

    ~raw_array();

  private:
    bool external;
    std::function<void(pointer_type)> free_fct;
  };
}
PYTHONIC_NS_END

#endif
