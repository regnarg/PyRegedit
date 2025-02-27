#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import shutil
import sys
import os
import wx


sys.path.append(os.path.abspath("../Models"))
sys.path.append(os.path.abspath("../Views"))

from Models import *
from Views import *

class Controller:

	title = "PyRegedit"
	
	def initApp(self):

		self.app = wx.PySimpleApp(0)
		self.frame = MainFrame(None, wx.ID_ANY, "")
		self.app.SetTopWindow(self.frame)
		
		self.sf = SetupFrame()
		self.sf.Show()
		
		self.sf.Bind(wx.EVT_BUTTON, self.OnFileButtonClick, self.sf.buttonFileSelect)
		self.sf.Bind(wx.EVT_BUTTON, self.reloadSetupView, self.sf.buttonReload)
		self.sf.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnSetupListClick, self.sf.lc)
		self.sf.Bind(wx.EVT_CLOSE, self.OnCloseSetup)
		
		# Init menu bar
		self.menuBar = MenuBar()
		self.frame.SetMenuBar(self.menuBar)
		self.initMenuBar()

		self.hivex = None
		self.editing = False
		self.ef = None
		self.firstSave = True
		self.saved = False
		
		#self.openHive("Data/NTUSER.DAT_key_types")
		#self.full_path = os.path.abspath("Data/NTUSER.DAT_key_types")

		# Init handle for TreeView
		self.treeView = self.frame.TreeView
		self.initTreeView()

		# Init handle for ListCtrl
		self.lc = self.frame.lc
		self.frame.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick, self.lc)

		#self.frame.Show()
		self.app.MainLoop()

	def setStatusBarText(self, text):
		self.frame.sb.SetStatusText(text)

	def openHive(self, path):
		
		self.hive = File(path)
		if(not self.hive.existsFile()):
			 wx.MessageBox('File not found!', 'Error', wx.OK | wx.ICON_ERROR)
			 return False			
		if(not self.hive.isFileHive()):
			 wx.MessageBox('File is not valid hive!', 'Error', wx.OK | wx.ICON_ERROR)
			 return False
			 
		self.hivex = HivexManager(self.hive);
		self.setStatusBarText("Hive opened: " + path)

		self.firstSave = True
	'''
		Kliknutí na list v Setupu
	'''
	def OnSetupListClick(self, event):
	
		item = event.GetItem()
		path_to_hive = item.GetText() # name of key
		
		self.openHive(path_to_hive)
		self.reloadTreeView()
		self.frame.Show()
		self.sf.Close()
		
	def OnCloseSetup(self, event):

		self.sf.Destroy()
		self.frame.Show()
		
	'''
		Click on selected key -> value
	'''
	def OnClick(self, event):
		
		if self.editing == True: 
			return False # existuje už dialog?

		item = event.GetItem()
		node = item.GetData() # parent node of this key
		keyName = item.GetText() # name of key

		value = self.hivex.getValue(node, keyName)

		self.initEditFrame(keyName, value[0]) # inicializace editačního dialogu
		
		vType = Type.TYPES[value[1]] # hodnota typu
		self.ef.rtype.SetValue(vType)
		
		# save values for saving
		#self.editingValue = { "key" : keyName, "t": value[1], "value" : value[0] }
		self.editingNode = node

		self.editing = True
		
	'''
		Saving value back to key
	'''
	def OnSaveClick(self, event):

		value = {}
		new_value = self.ef.key_value.GetValue()

		
		# reconvert
		value["key"] = self.ef.key_name.GetValue()
		value["t"] = [i for i, x in enumerate(Type.TYPES) if x == self.ef.rtype.GetValue()][0]

		if not self.checkValueType(value["t"], new_value):
			return False
		
		value["value"] = self.hivex.getIntepretationBack(value["t"], new_value)
		
		#print "saving", value
		self.hivex.setValue(self.editingNode, value)

		self.reloadKeyView(self.editingNode)
		self.ef.Close()
		
		self.editing = False
		self.editingNode = None
		self.ef = None
		#self.editingValue = None

		self.setStatusBarText("Key was saved")
		self.isSaved(False)

	def OnCancelClick(self, event):

		self.ef.Close()
		self.ef = None
		self.editing = False
		
	
	'''
		Menu Bar
	'''
	def initMenuBar(self):
		
		self.frame.Bind(wx.EVT_MENU, self.menuOpen, id=self.menuBar.ID_OPEN)
		self.frame.Bind(wx.EVT_MENU, self.menuClose, id=self.menuBar.ID_CLOSE)
		self.frame.Bind(wx.EVT_MENU, self.menuSave, id=self.menuBar.ID_SAVE)
		self.frame.Bind(wx.EVT_MENU, self.menuReload, id=self.menuBar.ID_RELOAD)
		self.frame.Bind(wx.EVT_MENU, self.menuAddNode, id=self.menuBar.ID_ADD_NODE)
		self.frame.Bind(wx.EVT_MENU, self.menuDeleteNode, id=self.menuBar.ID_DELETE_NODE)
		self.frame.Bind(wx.EVT_MENU, self.menuAddKey, id=self.menuBar.ID_ADD_KEY)
		self.frame.Bind(wx.EVT_MENU, self.menuRemoveKey, id=self.menuBar.ID_REMOVE_KEY)
		self.frame.Bind(wx.EVT_MENU, self.menuAbout, id=self.menuBar.ID_ABOUT)

	def menuOpen(self, event):
		
		self.dirname = ""
			
		dlg = wx.FileDialog(self.frame, "Choose a hive", self.dirname, "", "*", wx.FD_OPEN)
		
		if dlg.ShowModal() == wx.ID_OK:
			
			self.filename = dlg.GetFilename()
			self.dirname = dlg.GetDirectory()
			self.full_path = os.path.join(self.dirname, self.filename)
			print(self.full_path) # test
			self.openHive(self.full_path)
			self.reloadTreeView()

		dlg.Destroy()
	'''
		Otevření dialogu pro výběr složky v setupu
	'''
	def OnFileButtonClick(self, event):
		
		dlg = wx.DirDialog(self.sf, "Select a folder")
		
		if dlg.ShowModal() == wx.ID_OK:
			
			path = dlg.GetPath();
			# Uložíme lokaci do inputu
			self.sf.inputFile.SetValue(path)

		dlg.Destroy()		
	
	'''
		Reload a načtení soubor při setupu
	'''
	def reloadSetupView(self, event):
		
		path = self.sf.inputFile.GetValue()
		fullRegistryPath = os.path.join(path, "System32/config")
		
		if(not os.path.isdir(fullRegistryPath)):
			print("not directory" + fullRegistryPath)
			self.sf.textStatus.SetLabel("Not valid directory")
			return False
		
		self.sf.lc.DeleteAllItems()
		
		files = {
			"system": "HKEY_LOCAL_MACHINE\SYSTEM ", 
			"sam": "HKEY_LOCAL_MACHINE\SAM", 
			"security": "HKEY_LOCAL_MACHINE\SECURITY",
			"software": "HKEY_LOCAL_MACHINE\SOFTWARE",
			"default": "HKEY_USERS.DEFAULT"
		}
		i = 0
		# Prolezeme složku a najdeme hive files
		for key, value in files.items():
			
			found = False
			print(fullRegistryPath + "/" + key)
			
			if os.path.isfile(fullRegistryPath + "/" + key):
				print("Nalezen klic " + value)
				found = True
			
			
			data = "not found"
			if found:
				data = fullRegistryPath + "/" + key
				
			index = self.sf.lc.InsertStringItem(i, data)	
			self.sf.lc.SetStringItem(index, 1,  value)
			i = i + 1
			
		print("done")
		


	def menuAbout(self, event):
		AboutDialog()

	'''
		Reload tree view of nodes
	'''
	def menuReload(self, event):
		
		self.reloadTreeView()

	'''
		Add new key and his value
	'''
	def menuAddKey(self, event):

		print("add key")
		if self.editing == True: 
			return False # existuje už dialog?
					
		item = self.treeView.GetSelection()
		keyId = self.treeView.GetItemData(item)[0]
		if not keyId:
			keyId = self.hivex.getRoot()

		self.initEditFrame() # inicializace editačního dialogu
		self.ef.key_name.Enable(True)
		self.ef.SetTitle("Add new key")

		# save values for saving
		#self.editingValue = { "key" : keyName, "t": value[1], "value" : value[0] }
		
		self.editingNode = keyId
		self.editing = True
		self.isSaved(False)
		
		
		#event.Skip()
	'''
		Delete actual key from list
	'''
	def menuRemoveKey(self, event):

		itemNumber = self.lc.GetFocusedItem()
		
		item = self.lc.GetItem(itemNumber, 0)
		node = item.GetData() # parent node of this key
		keyName = item.GetText() # name of key

		if not keyName:
			return False

		self.hivex.deleteKey(int(node), keyName)
		self.reloadKeyView(node)

		self.setStatusBarText(keyName + " - Key was deleted")
		self.isSaved(False)
		
		
	'''
		Close hive and delete items in tree View
	'''
	def menuClose(self, event):

		if not self.saved:

			dlg = wx.MessageDialog(None, 'Your work is not saved!', 'Are you sure?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_YES:
				self.treeView.DeleteAllItems()
				self.hivex = None
				self.lc.DeleteAllItems()
			
	'''
		Save changes to hive
		- and create backup copy...
	'''
	def menuSave(self, event):	
			
		if self.firstSave == True:
			#shutil.copyfile(self.full_path, self.full_path + ".backup" ) # create file backup
			self.firstSave = False
			
		self.hivex.saveChanges(self.full_path)
		self.setStatusBarText("Changes in hive was saved")
		self.isSaved(True)

		
	'''
		Add new node to hive
	'''
	def menuAddNode(self, event):

		dlg = AddNodeDialog()
		if dlg.ShowModal() == wx.ID_OK:
			
			new_node = dlg.txt.GetValue()
			item = self.treeView.GetSelection()
			keyId = self.treeView.GetItemData(item)[0]
			newId =  self.hivex.addChild(keyId, new_node)

			self.treeView.SetItemData(item, [keyId, True])  # update expand
			self.treeView.AppendItem(item, new_node, data=[newId, False]) 

			self.setStatusBarText("Node was added")
			self.isSaved(False)
			
		dlg.Destroy()
		
	def menuDeleteNode(self, event):

		dlg = wx.MessageDialog(None, 'Are you sure to delete this node? And all his subnodes!', 'Are you sure?', 
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:

			item = self.treeView.GetSelection()
			keyId = self.treeView.GetItemData(item)[0]

			self.hivex.removeChild(keyId)
			self.treeView.Delete(item)

			self.setStatusBarText("Node was deleted")
			self.isSaved(False)

	'''
		Tree View
	'''
	def initTreeView(self):

		# Bind for collapse and uncollapse
		self.treeView.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpandItem)
		#self.treeView.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapseItem)	
		self.treeView.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivatedItem)
		self.treeView.Bind(wx.EVT_LEFT_UP, self.OnActivatedItem) 

		self.reloadTreeView()
	
	def reloadTreeView(self):

		self.treeView.DeleteAllItems()
		root = self.treeView.AddRoot("My Computer", data=[0, True])

		if(self.hivex != None):
			# Top levels keys
			for key in self.hivex.getRootKeys():
				temp = self.treeView.AppendItem(root, key[0], data=[key[2], False])
				if(key[1] == True):
					self.treeView.SetItemHasChildren(temp)		
		
	
	def OnExpandItem(self, event):
		
		item = event.GetItem()
		if not item.IsOk():
			item = self.treeView.GetSelection()
		
		itemData = self.treeView.GetItemData(item)

		keyId = itemData[0]
		expand = itemData[1]

		name = self.treeView.GetItemText(item)

		# Byl už tento klíč rozbalen? 
		if(expand == False):
			# Top levels keys
			for key in self.hivex.getKeyChildren(keyId):
				temp = self.treeView.AppendItem(item, key[0], data=[key[2], False])
				if(key[1] == True):
					self.treeView.SetItemHasChildren(temp)

			# Expand -> TRUE
			self.treeView.SetItemData(item, [keyId, True]) 
			
	
		
		#print "data: %i, name: %" % (data, name)
		
	'''
		Click on item and write his key -> values
	'''
	def OnActivatedItem(self, event):

		#item = event.GetItem()
		#if not item.IsOk():
		item = self.treeView.GetSelection()
		
		print(repr(self.treeView.GetItemData(item)))
		keyId = self.treeView.GetItemData(item)[0]
		
		if self.hivex:
		
			if not keyId:
				keyId = self.hivex.getRoot()
	
			self.reloadKeyView(keyId)
			
	'''
		Reload view of values
	'''
	def reloadKeyView(self, keyId):

		self.lc.DeleteAllItems()
		rows = self.hivex.getValues(keyId)
		
		for i, val in enumerate(rows):
			
			index = self.lc.InsertStringItem(i, val[0])
			self.lc.SetStringItem(index, 1, val[1])
			self.lc.SetStringItem(index, 2, val[2])

			self.lc.SetItemData(index, keyId)

	'''
		Init edit frame
	'''
	def initEditFrame(self, keyName = "", keyValue = ""):

		# Create frame for editing value
		self.ef = EditFrame()

		for type in Type.TYPES:
			self.ef.rtype.Append(type)

		self.ef.rtype.SetValue(Type.TYPES[1])
		
		self.ef.Bind(wx.EVT_BUTTON, self.OnSaveClick, self.ef.btn_save)
		self.ef.Bind(wx.EVT_BUTTON, self.OnCancelClick, self.ef.btn_cancel)

		self.ef.key_name.SetValue(keyName)
		self.ef.key_value.SetValue(str(keyValue))

		self.ef.Show()

	def checkValueType(self, val_type, value):

		value = value.strip()
		if val_type == Type.BINARY:
			'''try:
				int(value, 16)
			except Exception:
				self.throwErrorDialog("This is not valid hexadecimal value")
				return False'''
			return True
			
		elif val_type == Type.INTEGER_BIG_ENDIAN or val_type == Type.INTEGER:
			try:
				int(value)
			except Exception:
				self.throwErrorDialog("This is not valid INT value")
				return False

		return True

	def throwErrorDialog(self, message):
		wx.MessageBox(message, 'Error', wx.OK | wx.ICON_ERROR)
		
	
	def isSaved(self, saved):

		if saved == True:
			self.frame.SetTitle(self.title + " - SAVED")
		else:
			self.frame.SetTitle(self.title + " - Modified *")

		self.saved = saved
			

