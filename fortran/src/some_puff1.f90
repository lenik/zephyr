! Copyright (C) 2026 Lenik <zephyr@bodz.net>
! SPDX-License-Identifier: AGPL-3.0-or-later

program some_puff1
  use iso_fortran_env, only: error_unit, input_unit, output_unit
  use commons
  implicit none
  character(len=256) :: arg
  integer :: i, argc, status, verbose

  verbose = 0
  argc = command_argument_count()
  i = 1
  do while (i <= argc)
    call get_command_argument(i, arg)
    select case (trim(arg))
    case ('-h', '--help')
      call usage()
      stop
    case ('--version')
      call show_version()
      stop
    case ('-v', '--verbose')
      verbose = verbose + 1
    case ('-q', '--quiet')
      verbose = -1
    case default
      exit
    end select
    i = i + 1
  end do

  if (verbose > 0) write(error_unit, '(a)') 'some_puff1: verbose mode enabled'

  if (i > argc) then
    if (verbose > 0) write(error_unit, '(a)') 'some_puff1: reading from standard input'
    status = copy_stream(input_unit, output_unit)
    if (status /= 0) stop 1
    stop
  end if

  do while (i <= argc)
    call get_command_argument(i, arg)
    if (trim(arg) == '-') then
      if (verbose > 0) write(error_unit, '(a)') 'some_puff1: copying from standard input'
      status = copy_stream(input_unit, output_unit)
    else
      if (verbose > 0) write(error_unit, '(a,a)') 'some_puff1: copying from ', trim(arg)
      status = copy_file(trim(arg))
    end if
    if (status /= 0) stop 1
    i = i + 1
  end do
contains

  subroutine usage()
    write(output_unit, '(a)') &
      'Usage: some_puff1 [OPTION]... [FILE]...' // new_line('a') // &
      'Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,' // new_line('a') // &
      'read standard input.' // new_line('a') // new_line('a') // &
      '  -v, --verbose      repeat for more verbose loggings' // new_line('a') // &
      '  -q, --quiet        show less logging messages' // new_line('a') // &
      '  -h, --help         display this help and exit' // new_line('a') // &
      '      --version      output version information and exit' // new_line('a') // new_line('a') // &
      'Report bugs to: <zephyr@bodz.net>'
  end subroutine usage

  subroutine show_version()
    write(output_unit, '(a)') 'some_puff1 dev'
    write(output_unit, '(a)') 'Copyright (C) 2026 Lenik'
    write(output_unit, '(a)') 'License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>'
  end subroutine show_version

end program some_puff1
