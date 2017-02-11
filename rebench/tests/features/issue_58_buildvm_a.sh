#!/bin/bash
echo "#!/bin/bash" > vm_58a.sh
echo "echo \$@" >> vm_58a.sh
chmod +x vm_58a.sh
echo standard
echo error 1>&2