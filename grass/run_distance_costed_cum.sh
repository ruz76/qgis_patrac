PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
export PATH
unset PYTHONPATH
unset GISBASE
unset LD_LIBRARY_PATH
#printenv
python $2/grass/distance_costed_cum.py $1 $2 $3
