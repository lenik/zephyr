! Copyright (C) 2026 Lenik <zephyr@bodz.net>
! SPDX-License-Identifier: AGPL-3.0-or-later

program test_commons
  use commons
  implicit none
  integer :: u_in, u_out, ios

  open(newunit=u_in, file='test_commons.in', status='replace', action='write')
  write(u_in, '(a)') 'alpha'
  write(u_in, '(a)') 'beta'
  close(u_in)

  open(newunit=u_in, file='test_commons.in', status='old', action='read')
  open(newunit=u_out, file='test_commons.out', status='replace', action='write')
  ios = copy_stream(u_in, u_out)
  close(u_in)
  close(u_out)
  if (ios /= 0) stop 1

  open(newunit=u_in, file='test_commons.in', status='old', action='write')
  close(u_in, status='delete')
  open(newunit=u_out, file='test_commons.out', status='old', action='write')
  close(u_out, status='delete')
end program test_commons
