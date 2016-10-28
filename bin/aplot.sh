#!/bin/bash

print_help()
{
cat << EOF
 Plot AUTO bifdiagrams

 usage : $0 -d <auto dir> [OPTIONS]

 OPTIONS
 	-d <dir>     auto work directory
 	-v           open image, or not
 	-x <xtitle>  x-axis title
 	-y <ytitle>  y-axis title
 	-t <title>   title
 	-o <out.png> out png image
 	-c           print cmd for aplot.py
	-k <keys>    additional keys for aplot.py
EOF
}
dir=;
visual="";
xtitle="";
ytitle="";
title="";
width="";
height="";
out="";
cmd=false;
keys="";
while getopts "d:vx:y:t:o:w:h:ck:" OPTION; do
	case $OPTION in
		d)
			dir=$OPTARG;;
		v)
			visual="-v";;
		x)
			xtitle="--xtitle $OPTARG";;
		y)
			ytitle="--ytitle $OPTARG";;
		t)
			title="--title '$OPTARG'";;
		o)
			out="-o $OPTARG";;
		w)
			width="-x $OPTARG";;
		h)
			height="-y $OPTARG";;
		c)
			cmd=true;;
		k)
			keys="$OPTARG";;
		?)
			print_help
			exit -1;;
	esac
done

if [[ "${dir}" == "" ]]; then
	echo " error : auto work directory not set";
	echo;
	print_help;
	exit -1;
else
	if [[ ! -d ${dir} ]]; then
		echo " error : directory \`${dir}' not found";
		echo;
		print_help;
		exit -1;
	fi
fi


if ls ${dir}/{auto,runAuto.config} &>/dev/null; then
	dir="${dir}/auto";
fi

if [[ "${out}" == "" ]]; then
	out="-o ${dir}/fort.png";
fi

f7=();
f8=();
if [[ -f "${dir}/fort.7" && -f "${dir}/fort.8" ]]; then
	f7+=("${dir}/fort.7");
	f8+=("${dir}/fort.8");
fi

for f in `ls ${dir}/s.* 2>/dev/null | grep -v -F '~'`; do
	n=`basename $f | sed -r 's/s\.//'`;
	f7+=("${dir}/b.${n}");
	f8+=("${dir}/s.${n}");
done

pars=;
if [[ -f "${dir}/par_replace" ]]; then
	pars="-p ${dir}/par_replace";
fi

echo ${out} ${pars} ${visual} ${xtitle} ${ytitle} ${title}

if $cmd; then
	echo -n "/data/lib/pauto/bin/aplot.py ";
	for((i=0; i<${#f7[@]}; ++i)); do echo -n " -s${i} ${f8[$i]} -d${i} ${f7[$i]} "; done;
	echo ${out} ${pars} ${visual} ${xtitle} ${ytitle} ${title} ${width} ${height};
	exit 0;
fi


/data/lib/pauto/bin/aplot.py \
	`for((i=0; i<${#f7[@]}; ++i)); do echo -n " -s${i} ${f8[$i]} -d${i} ${f7[$i]}"; done` \
		${out} ${pars} ${visual} ${xtitle} ${ytitle} ${title} ${width} ${height} ${keys}
