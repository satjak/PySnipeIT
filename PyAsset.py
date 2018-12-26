#!/usr/bin/env python
#
#	PyAsset.py

__author__ = 'Jeff Korthuis (jeffkorthuis@gmail.com)'
__version___ = '0.4.0'

import json
import requests
import argparse
import logging
global myToken
global snipeURL
global jsonHeader
global defaultResults
defaultResults = ['id','asset_tag','name','serial','model_number','munki_roles','assigned_to','status_label','location']
snipeURL = 'https://assets.something.com/api/v1/'
myToken = 'Bearer token'
jsonHeader = 'application/json'

class API:
	#This is the main function. It assumes you know 1) the table you want + 2) the ID of the object you want
	def __init__(self,Table,ID):
		self.Table = Table
		self.ID = ID
		self.URL = snipeURL + str(Table) + "/" + str(ID)
		self.r = requests.get(self.URL,headers={'Authorization': myToken,'Content-Type':'application/json'})
	def __call__(self):
		return self.r.json()

class SEARCH:
	#This is the function that find the object you are looking for. Pass it any string, and any table and it will pass back the results of the search. This will always exit the script unless it returns only 1 result
	def __init__(self,Table,SearchString):
		self.Table = Table
		self.SearchString = SearchString
		self.URL = snipeURL + str(Table) + "?search=" + str(SearchString)
		self.Results = requests.get(self.URL,headers={'Authorization': myToken,'Content-Type':'application/json'})
	def __call__(self):
		###Searches can result in multipul values. If we only get 1 result back it is a succesfful search. Everything else will exit
		resultCount = self.Results.json()['total']
		if resultCount == 1:
			return self.Results.json()['rows'][0]
		else:
			results = self.Results.json()['rows']
			self.multipulResults(results,resultCount)

	def multipulResults(self,results,resultCount):
		#Multi Response Error Handling#
		if resultCount == 0:
			print "No results found for " + str(self.Table) + "search: " + str(self.SearchString)
			exit()
		else:
			print "Multi-Results found on search: " + self.URL
			for item in results:
				results = RETURN(item)
				print results()
			exit()

class CHECKIN:
	def __init__(self,hardwareInfo):
		self.hardwareInfo = hardwareInfo
		postData = {}
		postData['name'] = hardwareInfo['name']
		postData['note'] = userVariables.notes
		postFields = json.dumps(postData, sort_keys=True,indent=2)
		URL = snipeURL + 'hardware/' + str(hardwareInfo['id']) + "/checkin"
		r = requests.post(URL,headers={'Authorization': myToken,'Content-Type': jsonHeader},data=postFields)
		print r.json()['messages']

class CHECKOUT:
	def __init__(self,hardwareInfo,userInfo):
		self.hardwareInfo = hardwareInfo
		self.userInfo = userInfo
		postData = {}
		postData['name'] = self.hardwareInfo['name']
		postData['note'] = userVariables.notes
		postData['assigned_user'] = userInfo['id']
		postData['checkout_to_type'] = 'user'
		postFields = json.dumps(postData, sort_keys=True,indent=2)
		self.URL = snipeURL + 'hardware/' + str(hardwareInfo['id']) + "/checkout"
		if self.hardwareInfo['assigned_to']:
			checkinCMD = CHECKIN(hardwareInfo)
		r = requests.post(self.URL,headers={'Authorization': myToken,'Content-Type':'application/json'},data=postFields)
		itemInfo = RETURN(hardwareInfo)
		print itemInfo()
		print r.json()['messages']

class RETURN:
	def __init__(self, hardwareInfo):
		self.hardwareInfo = hardwareInfo
		self.results = {}
		for item in self.hardwareInfo:
			if item in defaultResults:
				if type(self.hardwareInfo[item]) == dict:
					self.results[item] = self.hardwareInfo[item]['name']
				else:
					self.results[item] = self.hardwareInfo[item]
		for item in self.hardwareInfo['custom_fields']:
			if item in defaultResults:
				self.results[item] = self.hardwareInfo['custom_fields'][item]['value']
	def __call__(self):
		return json.dumps(self.results, indent=2)

#####
#MAIN
#
class MainProcess():
	def iRUNFIRST(self):

		global userVariables
		########################setup the logger####################
		self.loggingSetup()
		logger.info("----PYASSETS BEGIN----")
		userVariables = self.getVariables()

		logger.info("Arguements passed: " + str(userVariables))

		if userVariables.function == 'get':
			searchRequest = SEARCH('hardware',userVariables.hardware)
			hardwareInfo = API('hardware',searchRequest()['id'])
			results = RETURN(hardwareInfo())
			print results()

		####CREATE####
		elif userVariables.function == 'create':
			print "I don't know how to do this yet"
			exit()

		####CHECKOUT####
		elif userVariables.function == 'checkout':
			searchRequest = SEARCH('hardware',userVariables.hardware)
			searchUser = SEARCH('users',userVariables.user)
			hardwareInfo = API('hardware',searchRequest()['id'])
			checkoutCMD = CHECKOUT(hardwareInfo(),searchUser())


		####CHECKIN####
		elif userVariables.function == 'checkin':
			searchRequest = SEARCH('hardware',userVariables.hardware)
			hardwareInfo = API('hardware',searchRequest()['id'])
			checkinCMD = CHECKIN(hardwareInfo())

		####FAIL####
		else:
			logger.info("You broke me. I don't know what - " + userVariables.function + " - is!")
			logger.info("----END RUN----")
			exit()

	def getVariables(self):
		parser = argparse.ArgumentParser(description='Hello and welcome to the PyAsset.py script. They is pretty much just a ghetto api thing. Enjoy.   Here is a sample command:  ./PyAssets.py --function get --hardware "C02M631GFH05" // this can be any unique item identifier ')
		parser.add_argument('-f','--function',type=str,help='REQUIRED: get, update, create, destroy, user')
		parser.add_argument('-i','--hardware',type=str,help='REQUIRED: The key value you are searching on')
		parser.add_argument('-u','--user',type=str,help='REQUIRED FOR CHECKOUT: example jak')
		parser.add_argument('-t','--testing',type=str,help='enter the super secret test loop')
		parser.add_argument('-n','--notes',type=str,help='Any notes you wish to append to checkin or checkout')
		parser.add_argument('-s','--status',type=str,help='Status of the asset after checkin our checkout')
		parser.add_argument('-q','--query',type=str,help='Return a specific result / results -- formatted "id,name,serial"')

		#######Item Creation / Update Values#########
		userVariables = parser.parse_args()
		if not userVariables.function:
			userVariables.function = raw_input("What function did you want to perform ('get','checkin','checkout'): ")
			if userVariables.function == 'checkout':
				userVariables.user = raw_input("Checkout to whom? ('jak'): ")
		if not userVariables.hardware:
			userVariables.hardware = response = raw_input("What asset are you going to perform it on? (provide a unique string i can search for): ")
		if not userVariables.notes:
			userVariables.notes = "Checkout by PyAsset Script"
		if not userVariables.query:
			pass
		else:
			my_list = [str(item) for item in userVariables.query.split(',')]
			global defaultResults
			defaultResults = my_list
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
