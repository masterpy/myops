i=0
while read ip
do 
  ping -c 2 -w 2 $ip > /dev/null
  if [ "$?" == "0" ]
  then
     echo $ip  >> ok
  else
      echo $ip >> not-ok
  fi
done < ip.list
