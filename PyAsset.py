#!/usr/bin/env python
#
#	PyAsset.py
#	Your one-stop shop for all asset stuff
# python PyAsset.py --MAC "78:31:c1:c1:c1:42" --function "get" --serial "C02M123GFH05" --model "MACBookPro11,1" --category "Laptops" --notes "testing testing 123" --status "Deployed" --DNS_name "jak-2131" --MAC_Eth0 "ac:87:a3:14:ce:03" --MAC_WiFi "78:31:c1:c1:76:42" --Munki_Manifest "satjak" --munki_roles "testing"

__author__ = 'Jeff Korthuis (jeffkorthuis@gmail.com)'
__version___ = '0.3.0'

import json
import requests
import argparse
import logging

class MainProcess():
	def iRUNFIRST(self):
		global myToken
		global userVariables
		global snipeURL
		global jsonHeader
		#########SYSTEM VARIABLES#########
		snipeURL = 'https://assets.something.com/api/v1/'
		defaultResults = ['id','asset_tag','name','serial','model_number','Mac_Address_(Ethernet)','Mac_Address_(WiFi)','Munki_Manifest','munki_roles','assigned_to','category','status_label','location']
		myToken = 'Bearer someapikey'
		jsonHeader = 'application/json'
		########################setup the logger####################
		self.loggingSetup()
		logger.info("----PYASSETS BEGIN----")
		userVariables = self.getVariables(defaultResults)
		logger.info("Arguements passed: " + str(userVariables))

		####################main process#####################
		####GET####
		if userVariables.function == 'get':
			self.getRun()

		####CREATE####
		elif userVariables.function == 'create':
			print "I don't know how to do this yet"
			exit()

		####CHECKOUT####
		elif userVariables.function == 'checkout':
			self.checkoutRun()

		####CHECKIN####
		elif userVariables.function == 'checkin':
			self.checkinRun()

		####FAIL####
		else:
			logger.info("You broke me. I don't know what - " + userVariables.function + " - is!")
			logger.info("----END RUN----")
			exit()

	def output(self,hardwareInfo):
		##########
		# inputs: hardwareInfo
		#
		#
		# Output: prints the information requested from
		# --query
		# --hardware
		allFields = {}
		global CustomFields
		CustomFields = self.getCustomFields()
		logger.info("Custom Fields Present in DB: " + str(CustomFields))
		for x in userVariables.query:
			try:
				if str(x) in CustomFields:  #If the value you are looking for is a custom field
					allFields[str(x)] = str(self.getCustomField(x,hardwareInfo))
				elif type(hardwareInfo[str(x)]) == dict: #elif it has a dictionary inside
					try:
						allFields[str(x)] = hardwareInfo[str(x)]['name']
					except:
						allFields[str(x)] = hardwareInfo[str(x)]
				else: #else it is just a plain field
					if hardwareInfo[str(x)]:
							allFields[str(x)] = str(hardwareInfo[str(x)])
					else: #maybe it is null
						allFields[str(x)] = ''
			except: #NONE OF THE ABOVE
				logger.info("The following field was non-existant or null: " + str(x))

		print json.dumps(allFields,sort_keys=True, indent=2)
		logger.info(json.dumps(allFields, indent=2))
		logger.info("----PYASSETS EXIT SUCCESSFUL----")

	def getRun(self):
		##########
		# inputs: None
		#
		#
		# Output: hardwareInfo
		#
		#
		logger.info("Function: 'getRun'" + " // " + str(userVariables.hardware))
		AssetID = self.getField('hardware',userVariables.hardware,'id')
		hardwareInfo = self.getInfo(AssetID,'hardware')
		logger.info("Finalizing output: // " + "AssetID: " + str(AssetID) + " // Asset_Tag: " + str(hardwareInfo['asset_tag']))
		getReturn = json.dumps(hardwareInfo, sort_keys=True,indent=2)
		self.output(hardwareInfo)

	def checkinRun(self):
		##########
		# inputs: None
		#
		#
		# Output: print of the results of a checkin
		#
		#
		logger.info("starting 'checkinRun'")
		AssetID = self.getField('hardware',userVariables.hardware,'id')
		logger.info("AssetID: " + str(AssetID))
		postData = {}
		postData['name'] = self.getInfo(AssetID,'hardware')['name']
		postData['note'] = userVariables.notes
		postFields = json.dumps(postData, sort_keys=True,indent=2)
		postURL = snipeURL + 'hardware/' + str(AssetID) + "/checkin"
		logger.info("Performing a checkin:  " + postFields)
		r = requests.post(postURL,headers={'Authorization': myToken,'Content-Type': jsonHeader},data=postFields)
		print r.json()['messages'] + " // "  + postData['name']

	def checkoutRun(self):
		##########
		# inputs: None
		#
		#
		# Output: print of the results of a checkout
		#
		#
		logger.info("Function: 'checkoutRun'")
		if not userVariables.user:
			print "please provide a username -u --user \"jak\""
			exit()
		AssetID = self.getField('hardware',userVariables.hardware,'id')
		UserID = self.getField('users',userVariables.user,'id')
		postData = {}
		hardwareInfo = self.getInfo(AssetID,'hardware')
		######################Construct a response#################
		postData['name'] = hardwareInfo['name']
		postData['note'] = userVariables.notes
		postData['assigned_user'] = UserID
		postData['checkout_to_type'] = 'user'
		postFields = json.dumps(postData, sort_keys=True,indent=2)
		##########################################################
		logger.info("Performing a checkout to user: " + str(UserID) + " // " + str(postFields))
		postURL = snipeURL + 'hardware/' + str(AssetID) + "/checkout"
		logger.info ("POST URL: " + str(postURL))
		if userVariables.testing == 'true':
			logger.info("THIS WAS A TEST RUN")
			print "Test Run"
		else:
			r = requests.post(postURL,headers={'Authorization': myToken,'Content-Type':'application/json'},data=postFields)
			print r.json()['messages'] + " // "  + str(hardwareInfo['name']) + "  //  " + str(self.getInfo(UserID,'users')['name'])
			if r.json()['messages'] == 'That asset is not available for checkout!':
				logger.info("----RUNNING CHECKIN-----")
				self.checkinRun()
				self.checkoutRun()

	def getField (self,Table,Lookup,LookupObject):
		##########
		# inputs:
		# Table = the api/v1/TABLE/
		# Lookup = the value that we are looking up. For instance with api/v1/users/ we would look up jak
		# Lookup Object: The field value you wish to get returned
		#
		# Example call: self.getField('hardware','some device','id') // this would return the ID of 'some device'
		logger.info("Function: 'getField'" + " // " +str(Table) + " // "+ str(Lookup) + " // "+ str(LookupObject) + " // ")
		searchURL = snipeURL + str(Table) + "?search=" + str(Lookup)
		r = requests.get(searchURL,headers={'Authorization': myToken,'Content-Type':'application/json'})
		foundItems = r.json()['total']

		#Multi Response Error Handling#
		if foundItems == 1:
			jsonResponse = r.json()['rows'][0]
			return jsonResponse[LookupObject]
		else:
			jsonResponse = r.json()['rows']
			print "ASSET TAG    //    ASSET NAME    //     ASSIGNED TO"
			print "--------------------------------------------------"
			for item in r.json()['rows']:
				try:
					print item['asset_tag'] + "    //    " + item['name'] + "    //   " + str(item['assigned_to']['name'])
					logger.info(item['asset_tag'] + "    //    " + item['name'] + "    //   " + str(item['assigned_to']['name']))
				except:
					print item['asset_tag'] +    "    //    " + item['name'] + "    //    None "
					logger.info(item['asset_tag'] + "    //    " + item['name']+ "    //    None "  )
			print "--------------------------------------------------"
			logger.info("----SYSTEM EXITED----")
			exit()

	def getInfo(self, ID,Table):
		##########
		# inputs:
		# ID: The ID value of a known api lookup location must be proided to this funtion
		# Table: the know table that we are looking up.
		# Output: a json blob of the output
		# Example call: self.getField('hardware','jak-mbp-2131','id') // this would return the ID of jak-mbp-2131
		logger.info("Function: gethardwareInfo " + " // " + str(ID) + " // " + str(Table))
		searchURL = snipeURL + Table + "/"+ str(ID)
		r = requests.get(searchURL,headers={'Authorization': myToken,'Content-Type':'application/json'})
		hardwareInfo = r.json()
		return hardwareInfo

	def testingRun(self, ID,Table):
		logger.info("Function: 'testingRun'")
		print "<-----TESTING----->"
		print "<-----TESTING----->"

	def getCustomFields(self):
		##########
		# inputs: None
		#
		# Output: a table with all the custom fields names in it
		custom_Fields = []
		searchURL = snipeURL + 'fields/'
		r = requests.get(searchURL,headers={'Authorization': myToken,'Content-Type':'application/json'})
		for field in r.json()['rows']:
			custom_Fields.append(str(field['name']))
		logger.info("Function: 'getCustomField" + " // " + str(custom_Fields))
		return custom_Fields

	def getCustomField(self,Field,HardwareInfo):
		##########
		# inputs:
		# Field - Custom Field Name
		# HardwareInfo - the JSON array from the function getField
		#
		# Output: the value of the FIELD provided
		#
		logger.info("Function: 'getCustomField'")
		logger.info("Looking for: " + str(Field))
		return HardwareInfo['custom_fields'][Field]['value']



############################################################Value Added functions##############################################################################
	def getVariables(self,defaultResults):
		parser = argparse.ArgumentParser(description='Hello and welcome to the PyAsset.py script. They is pretty much just a ghetto api thing. Enjoy.   Here is a sample command:  ./PyAssets.py --function get --hardware "C02M631GFH05" // this can be any unique item identifier ')
		parser.add_argument('-f','--function',type=str,help='REQUIRED: get, update, create, destroy, user')
		parser.add_argument('-i','--hardware',type=str,help='REQUIRED: The key value you are searching on')
		parser.add_argument('-u','--user',type=str,help='REQUIRED FOR CHECKOUT: example jak')
		parser.add_argument('-t','--testing',type=str,help='enter the super secret test loop')
		parser.add_argument('-n','--notes',type=str,help='Any notes you wish to append to checkin or checkout')
		parser.add_argument('-q','--query',type=str,help='The fields you wish to return formatted "id,name,serial,..." ')
		parser.add_argument('-s','--status',type=str,help='Status of the asset after checkin our checkout')


		#######Item Creation / Update Values#########
		userVariables = parser.parse_args()
		if not userVariables.function:
			userVariables.function = 'get'
		if not userVariables.query:
			userVariables.query = defaultResults
		else:
			my_list = [str(item) for item in userVariables.query.split(',')]
			userVariables.query = my_list
		return userVariables

	def loggingSetup(self):
		global logger
		logger = logging.getLogger('Python Asset Lookup') #define the name of your app
		global hdlr
		hdlr = logging.FileHandler('/tmp/PyAsset.log') #define the file you want to log to
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') #define how you want your log to look
		hdlr.setFormatter(formatter) #initite the formatter
		logger.addHandler(hdlr) #initiate the handler
		logger.setLevel(logging.INFO) #set the LEVEL of alert {warning, info}

def main():
	mainProcess = MainProcess()
	mainProcess.iRUNFIRST()

if __name__ == '__main__':
	main()
