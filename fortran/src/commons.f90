! Copyright (C) 2026 Lenik <zephyr@bodz.net>
! SPDX-License-Identifier: AGPL-3.0-or-later

module commons
  use iso_fortran_env, only: error_unit, input_unit, output_unit
  implicit none
contains

  integer function copy_stream(unit_in, unit_out) result(status)
    integer, intent(in) :: unit_in, unit_out
    character(len=1) :: ch
    integer :: ios

    status = 0
    do
      read(unit_in, '(a1)', advance='no', iostat=ios) ch
      if (ios < 0) exit
      if (ios > 0) then
        status = 1
        return
      end if
      write(unit_out, '(a1)', advance='no', iostat=ios) ch
      if (ios /= 0) then
        status = 1
        return
      end if
    end do
  end function copy_stream

  integer function copy_file(path) result(status)
    character(len=*), intent(in) :: path
    integer :: u, ios

    status = 0
    open(newunit=u, file=path, status='old', action='read', iostat=ios)
    if (ios /= 0) then
      status = 1
      return
    end if
    status = copy_stream(u, output_unit)
    close(u)
  end function copy_file

end module commons
