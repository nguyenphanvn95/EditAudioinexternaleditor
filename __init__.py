'''
This addon opens one or many audios in an editor (the default is Audacity).
It supports 3 modes to choose which audios it opens. The config is entered in a text box and the searching mode will automatically detected.
If users enter "first_field,second_field,third_field", this addon will open every audios in "first_field" and "second_field"
If users enter "1,2:1", this addon will opens the first and second audios in the front card and the first audio in the back card.
If users enter "<div id=“editable”>[sound: … ]</div>" and tick the regex box, it will search audios that are surrounded by <div id="editable"> tag.
On main window -> only show change path button
On review mode, only show search fields
First, implement search box
Which information do we need to save?
    searchCriteria = {}
    searchCriteria["search_by_fields] = []
    searchCriteria["search_by_number] = ([number in the front card], [number in the back card])
    searhcCriteria["search_by_regex] = regex

'''
import os
import sys
import re
import anki
import aqt

from aqt.qt import *
from aqt import utils, mw
import subprocess
import shlex
from pickle import load, dump


dialog = None
soundRegex = re.compile("\[sound:(.*?\.(?:mp3|m4a|wav))\]")


class AddonDialog(QDialog):

    """Main Options dialog"""
    def __init__(self, config, configFile):
        QDialog.__init__(self, parent=mw)

        self.configFile = configFile
        self.config = config
        #self.loadConfig()
        self.setupUi()

    
    def setupUi(self):
        """Set up widgets and layouts"""
        deckLabel = QLabel("Choose deck")
        fieldLabel = QLabel("Fields in this deck")
        searchboxLabel = QLabel("Criteria search")
        editorPathLabel = QLabel("Editor path")
        deck = mw.col.decks.current()['name']
        self.criteriaBox = QLineEdit(self)
        self.fieldInfo = QLabel("\n".join(self.selectFields(deck)))
        self.searchByRebexCheckbox = QCheckBox("By regex")
        self.editorPath = QLabel(self.config["editor_path"])
        self.changeEditorPath = QPushButton("Change editor path")
        self.changeEditorPath.clicked.connect(self.handleChangePath)
        self.deckSelection = QComboBox()
        self.deckSelection.addItems(self.getDeckList())
        self.deckSelection.currentIndexChanged.connect(self.handleSelectDeck)
        self.criteriaBox.setText(self.getConfigValue())

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.addWidget(deckLabel, 1, 0)
        self.grid.addWidget(self.deckSelection, 1, 1)
        self.grid.addWidget(fieldLabel, 2, 0)
        self.grid.addWidget(self.fieldInfo, 2, 1)
        self.grid.addWidget(searchboxLabel, 3, 0)
        self.grid.addWidget(self.criteriaBox, 3, 1)
        self.grid.addWidget(self.searchByRebexCheckbox, 3, 2)
        self.grid.addWidget(editorPathLabel, 4, 0)
        self.grid.addWidget(self.editorPath, 4, 1)
        self.grid.addWidget(self.changeEditorPath)
        self.saveConfig = QCheckBox("Save config")

        # Main button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Help)
        buttonBox.accepted.connect(self.onAccept)
        buttonBox.rejected.connect(self.onReject)
        buttonBox.helpRequested.connect(self.handleShowHelp)

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(self.grid)
        mainLayout.addWidget(buttonBox)
        mainLayout.addWidget(self.saveConfig)
        self.setLayout(mainLayout)
        self.setMinimumWidth(360)
        self.setWindowTitle('Config edit audios in external editor')
    

    def getConfigValue(self):
        deck = self.deckSelection.currentText()
        if self.config is None or deck not in self.config:
            return ""
        
        config = self.config[deck]
        if "search_by_regex" in config:
            return config["search_by_regex"]

        if "search_by_number" in config:
            front, back = config["search_by_number"]
            return ','.join(front) + ':' + ','.join(back)

        if "search_by_fields" in config:
            fields = config["search_by_fields"]
            return ','.join(fields)

        return ""


    def handleSelectDeck(self):
        deck = self.deckSelection.currentText()
        self.criteriaBox.setText(self.getConfigValue())
        fields = self.selectFields(deck)
        self.fieldInfo.setText("\n".join(fields))


    def getDeckList(self):
        deckNames = sorted(mw.col.decks.allNames())
        currentDeck = mw.col.decks.current()['name']
        deckNames.insert(0, currentDeck)
        for i in range(len(deckNames)):
            if deckNames[i] == 'Default':
                deckNames.pop(i)
                break
        return deckNames


    def handleChangePath(self):
        dialog = OpenFileDialog()
        if isinstance(dialog.filename, list):
            path = dialog.filename[0]
        else:
            path = dialog.filename

        if path:
            if not anki.utils.isWin and '/' in path:
                path = path.split('/')[-1]

            utils.showInfo("Choose editor successful.")
            self.editorPath.setText(path)
            self.config["editor_path"] = path
            with open(configFile, 'wb') as f:
                dump(self.config, f)


    def handleShowHelp(self):
        utils.showText("""
            This addon opens one or many audios in an editor (the default is Audacity).
            It supports 3 modes to choose which audios it opens. The config is entered in a text box and the searching mode will automatically detected.
            If users enter "first_field,second_field,third_field", this addon will open every audios in "first_field" and "second_field"
            If users enter "1,2:1", this addon will opens the first and second audios in the front card and the first audio in the back card.
            If users enter "<div id=“editable”>[sound: … ]</div>" and tick the regex box, it will search audios that are surrounded by <div id="editable"> tag.
            You can also change the default audio editor. Now it is having a subtle bug with MacOS that crashes the editor (other than Audacity) when we edit the audios. In that case, you need to reopen the editor and crash Shift+G again.
        """)


    def selectFields(self, deck):
        query = 'deck:"{}"'.format(deck)
        cardId = mw.col.findCards(query=query)[0]
        card = mw.col.getCard(cardId)

        note = card.note()
        model = note.model()
        fields = card.note().keys()
        return fields
    

    def onAccept(self):
        ## 1. Get search field
        criteria = self.criteriaBox.text()
        if len(criteria) > 0:
            parsedCriteria = self.parseCriteria(criteria, self.searchByRebexCheckbox.isChecked())
            if parsedCriteria is None:
                utils.showInfo("Your input has an invalid form. Check the help for more detail about the input pattern.")
                return

            ## 2. Setup the config
            deck = self.deckSelection.currentText()
            self.config[deck] = parsedCriteria

        ## 3. If the save to default is checked, save the config to the config file
        if self.saveConfig.isChecked():
            with open(self.configFile, 'wb') as f:
                dump(self.config, f)
        
        self.close()

    
    def parseCriteria(self, criteria, searchByRegex=False):
        if searchByRegex:
            return self.parseByRegex(criteria)

        searchByNumberRegex = "^([1-9]+,)*[1-9]*:([1-9]+,)*[1-9]*$" 
        if re.match(searchByNumberRegex, criteria):
            return self.parseByNumber(criteria)

        searchByFieldRegex = "^(.+,)*.+$"
        if re.match(searchByFieldRegex, criteria):
            return self.parseByField(criteria)

        return None


    def parseByNumber(self, criteria):
        frontCard, backCard = criteria.split(":")
        frontCardAudios, backCardAudios = frontCard.split(','), backCard.split(',')
        searchCriteria = {}
        searchCriteria["search_by_number"] = (frontCardAudios, backCardAudios)
        return searchCriteria

    
    def parseByRegex(self, criteria):
        searchCriteria = {}
        searchCriteria["search_by_regex"] = criteria
        return searchCriteria


    def parseByField(self, criteria):
        fields = criteria.split(',')
        searchCriteria = {}
        searchCriteria["search_by_fields"] = fields
        return searchCriteria


    def onReject(self):
        self.close()


class OpenFileDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self, mw)
        self.title = 'Open file'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.filename = None
        self._init_ui()
    

    def _init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.filename = self._get_file()
        # self.exec_()
    

    def _get_file(self):
        if anki.utils.isWin:
            directory = os.path.expanduser("~/Desktop")
        else:
            directory = "/Applications"
        try:
            if anki.utils.isWin:
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                path = QFileDialog.getOpenFileName(self, "Open File", directory, "", options=options)
                if path:
                    return path
                else:
                    utils.showInfo("Cannot open this file.")
            else:
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                options |= QFileDialog.ShowDirsOnly 
                options |= QFileDialog.DontResolveSymlinks
                path = QFileDialog.getExistingDirectory(self, "Open Application", directory, options=options)
                if path:
                    return path
                else:
                    utils.showInfo("Cannot open this file.")

        except Exception as e:
            utils.showInfo(str(e))
            return None


def findFieldAudios(card):
    global soundRegex
    fldAudios = {}
    for field, value in card.note().items():
        matchAudios = soundRegex.findall(value)
        if matchAudios:
            fldAudios[field] = []
            for audio in matchAudios:
                fldAudios[field].append(audio)
    return fldAudios


def findSearchCriteria():
    global config
    ## current deck
    deck = mw.col.decks.current()['name']
    ## default mode
    searchCriteria = {"search_by_number": (['1',],['1',])}
    if (config is not None) and (deck in config):
        searchCriteria = config[deck]

    return searchCriteria


def findEditorPath():
    global config
    editorPath = config["editor_path"]
    return editorPath


def getFieldInTemplate(tmpl):
    fields = []
    start = 0
    while True:
        s = tmpl.find('{{', start)
        if s == -1: break
        e = tmpl.find('}}', s)
        if e != -1:
            fields.append(tmpl[s + 2:e][:])
            start = e + 2
        else: break
    return fields


def filterAudios(fields, fieldAudios, keptAudios):
    audios = []
    for field in fields:
        if field in fieldAudios:
            audios.extend(fieldAudios[field])

    for i in range(len(audios),0,-1):
        if str(i) not in keptAudios:
            del audios[i-1]

    return audios


def searchByNumber(numbers, card):
    fieldAudios = findFieldAudios(card)
    t = card.note().model()['tmpls'][card.ord]
    if aqt.mw.reviewer.state == 'question':
        ## audios for front card
        frontFields = getFieldInTemplate(t.get('qfmt'))
        return filterAudios(frontFields, fieldAudios, numbers[0])
    else:
        ## audios for back card
        backFields = getFieldInTemplate(t.get('afmt'))
        return filterAudios(backFields, fieldAudios, numbers[1])


def searchByFields(fields, card):
    fieldAudios = findFieldAudios(card)
    audios = []
    for field in fields:
        if field in fieldAudios:
            audios.extend(fieldAudios[field])

    return audios


def searchByRegex(regex, card):
    ## find by specified regex -> find by sound regex
    compiledRe = re.compile(regex)
    audios = []
    for field, value in card.note().items():
        matches = compiledRe.findall(value)
        if matches:
            for match in matches:
                matchedAudios = soundRegex.findall(match)
                for audio in matchedAudios:
                    audios.append(audio)
    return audios


def findAudiosToOpen(searchCriteria, card):
    if "search_by_regex" in searchCriteria:
        return searchByRegex(searchCriteria["search_by_regex"], card)

    if "search_by_number" in searchCriteria:
        return searchByNumber(searchCriteria["search_by_number"], card)

    if "search_by_fields" in searchCriteria:
        return searchByFields(searchCriteria["search_by_fields"], card)

    
def openAudios(editorPath, audios):
    global config, configFile
    ## use path to open editor and audios
    audioPaths = ['%s' % os.path.join(aqt.mw.col.media.dir(), audio) for audio in audios]
    for path in audioPaths:
        if not os.path.exists(path):
            utils.showInfo("file %s does not exist" % path)
            return

    if anki.utils.isWin:
        #Windows_SND = u'''start "" "%s" "%s"'''
        params = ["start", "", editorPath]
        params.extend(audioPaths)
        subprocess.call(params, shell=True)
    else:
        params = ["open", "-a", editorPath]
        params.extend(audioPaths)
        code = subprocess.call(params)
        if code > 0:
            utils.showInfo("Cannot open %s. Choose another editor" % editorPath)
            dialog = OpenFileDialog()
            if isinstance(dialog, list):
                path = dialog.filename[0]
            else:
                path = dialog.filename

            if path:
                if not anki.utils.isWin and '/' in path:
                    path = path.split('/')[-1]

                utils.showInfo("Choose editor successful.")
                config["editor_path"] = path
                with open(configFile, 'wb') as f:
                    dump(config, f)


def handleOpenAudios():
    ## if not review mode -> do nothing
    ## if review mode 
    ##      -> check if dialog is None or dialog.config has config[deck]
    ##      if have -> select audio based on that config
    ##      else use default config 1:1
    loadConfig()
    card = aqt.mw.reviewer.card
    if card is None:
        utils.showInfo("You are only able to open audios when you are reviewing cards.")
        return

    searchCriteria = findSearchCriteria()
    editorPath = findEditorPath()
    audiosToOpen = findAudiosToOpen(searchCriteria, card)
    openAudios(editorPath, audiosToOpen)


def handleConfig():
    global config, configFile
    loadConfig()
    dialog = AddonDialog(config, configFile)
    config = dialog.config
    dialog.exec()


config = {}
configFile = ""
def loadConfig():
    global config, configFile
    if len(configFile) > 0:
        return

    configFile = os.path.join(aqt.mw.col.media.dir(), "editAudio.cfg")
    config["editor_path"] = "/Applications/Audacity.app"
    if anki.utils.isWin:
        config["editor_path"] = "C:\\Program Files (x86)\\Audacity\\audacity.exe"

    if os.path.exists(configFile):
        with open(configFile, 'rb') as f:
            try:
                config = load(f)
            except:
                utils.showInfo("cannot load the config")


menu = mw.form.menuTools.addMenu("Edit audios in editor")

action = QAction("Edit audios", aqt.mw)
action.setShortcut(QKeySequence('alt+g'))
action.triggered.connect(handleOpenAudios)
menu.addAction(action)

action = QAction("Config", aqt.mw)
action.setShortcut(QKeySequence('shift+g'))
action.triggered.connect(handleConfig)
menu.addAction(action)
