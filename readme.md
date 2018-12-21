

#Required for a a return#
```
'-f','--function',type=str,help='REQUIRED: get, update, create, destroy, user'
'-i','--hardware',type=str,help='REQUIRED: The key value you are searching on'
```
#required for checkout or checkin
```
'-u','--user',type=str,help='REQUIRED FOR CHECKOUT: example jak'
'-t','--testing',type=str,help='enter the super secret test loop'
'-n','--notes',type=str,help='Any notes you wish to append to checkin or checkout'
```
#additional Fields
```
'-q','--query',type=str,help='The fields you wish to return formatted "id,name,serial,..." '
'-s','--status',type=str,help='Status of the asset after checkin our checkout'
```
#example
```
python ./PyAsset.py --function get --hardware '00:41:11:22:33:44'
```
