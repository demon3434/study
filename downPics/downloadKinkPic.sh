#!/bin/sh
#comments

currentPath=`pwd`
echo "#当前路径：${currentPath}"
echo "#完整命令格式：${0} 参数1(番号数字) 参数2(图片个数,默认40)"


#番号
fanhao=
if [ ! -n "${1}" ] 
then
	echo "请输入番号数字："
	read input
	fanhao=${input}
else
	fanhao=${1}
fi

#图片个数
count=
if [ ! -n "${2}" ]
then
	count=40
	echo "您没有指定图片个数，默认${count}个"
else
	count=${2}
fi

echo "当前下载任务：****  番号：${fanhao}  ****  预设图片个数：${count}  ****"


#生成下载批量下载图片的HTML网页
localHtmlFileName="downloadKinkPic.html"
if [  -f "${localHtmlFileName}" ]
then
	#echo "html文件已存在"
	rm  ${localHtmlFileName}
fi
touch  ${localHtmlFileName}
#echo "" > ./downloadKinkPic.html
echo "<html>" >> ${currentPath}/${localHtmlFileName}
echo "<head>" >> ${currentPath}/${localHtmlFileName}
echo "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />" >>  ${localHtmlFileName}
echo "<title>kink图片批量下载</title>" >> ${currentPath}/${localHtmlFileName}
echo "</head>" >> ${currentPath}/${localHtmlFileName}
echo "<body>" >> ${currentPath}/${localHtmlFileName}
index=0
remoteJpgFilename=
while [ ${index} -lt ${count} ]
do
	remoteJpgFilename="https://cdnp.kink.com/imagedb/${fanhao}/i/h/830/${index}.jpg"
	#echo ${remoteJpgFilename}
	echo "<a href=\"${remoteJpgFilename}\">${remoteJpgFilename}</a><br>" >> ${currentPath}/${localHtmlFileName}
	#statusCode=`curl -o /dev/null -s -w %{http_code} ${remoteJpgFilename}`
	#if [ ${statusCode} -eq "200" ]
	#then
		#echo ${remoteJpgFilename}
		#echo "<a href=\"${remoteJpgFilename}\">${remoteJpgFilename}</a><br>" >> ${currentPath}/${localHtmlFileName}
	#fi
	index=$((${index}+1))
done
echo "</body>" >> ${currentPath}/${localHtmlFileName}
echo "</html>" >> ${currentPath}/${localHtmlFileName}

echo "已在当前目录下，生成番号${fanhao}的图片批量下载网页，文件名\"downloadKinkPic.html\""


#生成用于wget或curl命令批量下载的txt文件
#localTxtFileName="downloadKinkPic.txt"
#if [  -f "${localTxtFileName}" ]
#then
#	#echo "html文件已存在"
#	rm  ${localTxtFileName}
#fi
#touch  ${localTxtFileName}
#index=0
#remoteJpgFilename=""
#while [ ${index} -lt ${count} ]
#do
#	remoteJpgFilename="https://cdnp.kink.com/imagedb/${fanhao}/i/h/830/${index}.jpg"
#	#echo ${remoteJpgFilename}
#	echo ${remoteJpgFilename} >> ${currentPath}/${localTxtFileName}
#	index=$((${index}+1))
#done

#echo "已在当前目录下，生成番号${fanhao}的图片URL的txt文件，文件名\"downloadKinkPic.txt\""


#让用户决定是否要通过shell下载
#curl命令详解网址：http://man.linuxde.net/curl
read -p "是否让shell来下载图片？Y或N（默认为N）" input
if [ "${input}" = "N" ] || [ "${input}" = "n" ]
then
	echo "您选择不用shell下载"
elif [ "${input}" = "Y" ] || [ "${input}" = "y" ]
then
	#用curl循环遍历下载
	if [ ! -d "${currentPath}/${fanhao}" ]
	then
		mkdir ${fanhao}
	fi
	cd ${currentPath}/${fanhao}
	echo "开始下载kink图片"
	index=0
	while [ ${index} -lt ${count} ]
	do
		remoteJpgFilename="https://cdnp.kink.com/imagedb/${fanhao}/i/h/830/${index}.jpg"
		echo  "当前图片：${remoteJpgFilename} ** \c"
		#如果当前目录下有同名文件，视为已下载过，跳过
		if [ -f "${currentPath}/${fanhao}/${index}.jpg" ]
		then
			echo "图片已下载"
			index=$((${index}+1))
			continue
		fi
		statusCode=$(curl -I -o /dev/null -s -w '%{http_code}' --retry 10 --retry-delay 1 --referer "https://www.kink.com/shoot/${fanhao}" --user-agent "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0" ${remoteJpgFilename})
		if [ ${statusCode} -eq 200 ]
		then
			httpResponseStr=$(curl -o ${currentPath}/${fanhao}/${index}.jpg --silent -O -w '%{http_code}:%{time_connect}:%{time_starttransfer}:%{time_total}'  --remote-time --retry 10 --retry-delay 1 --referer "https://www.kink.com/shoot/${fanhao}" --user-agent "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0" ${remoteJpgFilename})
			statusCode=$(echo ${httpResponseStr} | cut -d ":" -f 1)
			timeTotal=$(echo ${httpResponseStr} | cut -d ":" -f 4)
			#timeTotal=$(curl -o ${currentPath}/${fanhao} -s -w %{time_total} ${remoteJpgFilename})
			if [ ${statusCode} -eq 200 ]
			then
				echo "下载成功，耗时${timeTotal}秒"
			else
				echo "下载失败"
			fi
		else
			echo "远程文件不存在"
		fi
		#wget ${remoteJpgFilename} -P ${currentPath}/${fanhao} -q -c --tries 3
		#echo ${?}
		#if [ -f "${currentPath}/${fanhao}/${index}.jpg" ]
		#then
		   # echo "下载成功"
		#else
			#echo "下载失败"
		#fi
		index=$((${index}+1))
	done
	#从txt文件读取，批量下载
	#wget -i ${currentPath}/${localTxtFileName} -P ${currentPath}/${fanhao} -q -c --tries 3 -T
	echo "下载任务已结束"
else
	echo "默认不用shell下载"
fi


