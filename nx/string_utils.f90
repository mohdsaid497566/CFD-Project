module string_utils
  implicit none

  interface f_c_string
    module procedure f_c_string_char
  end interface

contains

  ! Convert a Fortran string to a C string
  function f_c_string_char(f_string) result(c_string)
    use, intrinsic :: iso_c_binding, only: c_char, c_null_char
    character(len=*), intent(in) :: f_string
    character(kind=c_char,len=:), allocatable :: c_string
    
    c_string = trim(f_string) // c_null_char
  end function
  
end module string_utils
