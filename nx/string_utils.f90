module string_utils
    use iso_c_binding
    implicit none

    contains
        function f_c_string(f_string) result(c_string)
            character(len=*), intent(in) :: f_string
            character(kind=c_char, len=:), allocatable :: c_string
            integer :: i, n
            
            n = len_trim(f_string)
            allocate(character(kind=c_char, len=n+1) :: c_string)
            
            do i = 1, n
                c_string(i:i) = f_string(i:i)
            end do
            c_string(n+1:n+1) = c_null_char
        end function f_c_string
end module string_utils
