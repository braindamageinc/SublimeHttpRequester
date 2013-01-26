import httplib
import sublime_plugin
import socket

gPrevHttpRequest = ""


class HttpRequester():

    REQUEST_TYPE_GET = "GET"
    REQUEST_TYPE_POST = "POST"
    REQUEST_TYPE_DELETE = "DELETE"
    REQUEST_TYPE_PUT = "PUT"

    httpRequestTypes = [REQUEST_TYPE_GET, REQUEST_TYPE_POST, REQUEST_TYPE_PUT, REQUEST_TYPE_DELETE]

    HTTP_URL = "http://"
    HTTPS_URL = "https://"

    httpProtocolTypes = [HTTP_URL, HTTPS_URL]

    HTTP_POST_BODY_START = "POST_BODY:"

    CONTENT_LENGTH_HEADER = "Content-lenght"

    FILE_TYPE_HTML = "html"
    FILE_TYPE_JSON = "json"
    FILE_TYPE_XML = "xml"
    httpContentTypes = [FILE_TYPE_HTML, FILE_TYPE_JSON, FILE_TYPE_XML]

    def __init__(self, resultsPresenter):
        self.resultsPresenter = resultsPresenter

    def request(self, selection):
        DEFAULT_TIMEOUT = 10
        FAKE_CURL_UA = "curl/7.21.0 (i486-pc-linux-gnu) libcurl/7.21.0 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.15 libssh2/1.2.6"
        MY_UA = "python httpRequester 1.0.0"

        lines = selection.split("\n")

        # trim any whitespaces for all lines and remove lines starting with a pound character
        for idx in range(len(lines) - 1, -1, -1):
            lines[idx] = lines[idx].lstrip()
            lines[idx] = lines[idx].rstrip()
            if (len(lines[idx]) > 0):
                if lines[idx][0] == "#":
                    del lines[idx]

        # get request web address and req. type from the first line
        (url, port, request_page, requestType, httpProtocol) = self.extractRequestParams(lines[0])

        print "Requesting...."
        print requestType, " ", httpProtocol, " HOST ", url, " PORT ", port, " PAGE: ", request_page

        #get request headers from the lines below the http address
        (extra_headers, requestPOSTBody) = self.extractExtraHeaders(lines)

        headers = {"User-Agent": FAKE_CURL_UA, "Accept": "*/*"}

        for key in extra_headers:
            headers[key] = extra_headers[key]

        # if valid POST body add Content-lenght header
        if len(requestPOSTBody) > 0:
            headers[self.CONTENT_LENGTH_HEADER] = len(requestPOSTBody)

        for key in headers:
            print "REQ HEADERS ", key, " : ", headers[key]

        # make http request
        try:
            if httpProtocol == self.HTTP_URL:
                conn = httplib.HTTPConnection(url, port, timeout=DEFAULT_TIMEOUT)
            else:
                conn = httplib.HTTPSConnection(url, port, timeout=DEFAULT_TIMEOUT)

            conn.request(requestType, request_page, requestPOSTBody, headers)
            resp = conn.getresponse()
            (respText, fileType) = self.getParsedResponse(resp)
            conn.close()
        except (socket.error, httplib.HTTPException) as e:
            respText = "Error connecting: " + e.strerror
        except AttributeError as e:
            print e
            respText = "HTTPS not supported by your Python version"

        self.resultsPresenter.createWindowWithText(respText, fileType)

    def extractHttpRequestType(self, line):
        for type in self.httpRequestTypes:
            if line.find(type) == 0:
                return type

        return ""

    def extractWebAdressPart(self, line):
        webAddress = ""
        for protocol in self.httpProtocolTypes:
            requestPartions = line.partition(protocol)
            if requestPartions[1] == "":
                webAddress = requestPartions[0]
            else:
                webAddress = requestPartions[2]
                return (webAddress, protocol)

        return (webAddress, self.HTTP_URL)

    def extractRequestParams(self, requestLine):
        requestType = self.extractHttpRequestType(requestLine)
        if requestType == "":
            requestType = self.REQUEST_TYPE_GET
        else:
            partition = requestLine.partition(requestType)
            requestLine = partition[2].lstrip()

        # remove http:// or https:// from URL
        (webAddress, protocol) = self.extractWebAdressPart(requestLine)

        request_parts = webAddress.split("/")
        request_page = ""
        if len(request_parts) > 1:
            for idx in range(1, len(request_parts)):
                request_page = request_page + "/" + request_parts[idx]
        else:
            request_page = "/"

        url_parts = request_parts[0].split(":")

        url_idx = 0
        url = url_parts[url_idx]

        if protocol == self.HTTP_URL:
            port = httplib.HTTP_PORT
        else:
            port = httplib.HTTPS_PORT

        if len(url_parts) > url_idx + 1:
            port = int(url_parts[url_idx + 1])

        # convert requested page to utf-8 and replace spaces with +
        request_page = request_page.encode('utf-8')
        request_page = request_page.replace(' ', '+')

        return (url, port, request_page, requestType, protocol)

    def getHeaderNameAndValueFromLine(self, line):
        readingPOSTBody = False

        line = line.lstrip()
        line = line.rstrip()

        if line == self.HTTP_POST_BODY_START:
            readingPOSTBody = True
        else:
            header_parts = line.split(":")
            if len(header_parts) == 2:
                header_name = header_parts[0].rstrip()
                header_value = header_parts[1].lstrip()
                return (header_name, header_value, readingPOSTBody)

        return (None, None, readingPOSTBody)

    def extractExtraHeaders(self, headerLines):
        requestPOSTBody = ""
        readingPOSTBody = False
        lastLine = False
        numLines = len(headerLines)

        extra_headers = {}
        if len(headerLines) > 1:
            for i in range(1, numLines):
                lastLine = (i == numLines - 1)
                if not(readingPOSTBody):
                    (header_name, header_value, readingPOSTBody) = self.getHeaderNameAndValueFromLine(headerLines[i])
                    if header_name != None:
                        extra_headers[header_name] = header_value
                else:  # read all following lines as HTTP POST body
                    lineBreak = ""
                    if not(lastLine):
                        lineBreak = "\n"

                    requestPOSTBody = requestPOSTBody + headerLines[i] + lineBreak

        return (extra_headers, requestPOSTBody)

    def getParsedResponse(self, resp):
        fileType = self.FILE_TYPE_HTML
        resp_status = "%d " % resp.status + resp.reason + "\n"
        respText = resp_status

        for header in resp.getheaders():
            respText += header[0] + ":" + header[1] + "\n"

            # get resp. file type (html, json and xml supported). fallback to html
            if header[0] == "content-type":
                fileType = self.getFileTypeFromContentType(header[1])

        respText += "\n\n\n"
        respBody = resp.read()
        respText += respBody.decode("utf-8", "replace")

        return (respText, fileType)

    def getFileTypeFromContentType(self, contentType):
        fileType = self.FILE_TYPE_HTML
        contentType = contentType.lower()

        print "File type: ", contentType

        for cType in self.httpContentTypes:
            if cType in contentType:
                fileType = cType

        return fileType


class HttpRequesterRefreshCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        print "here"
        global gPrevHttpRequest
        selection = gPrevHttpRequest

        resultsPresenter = ResultsPresenter(self)
        httpRequester = HttpRequester(resultsPresenter)
        httpRequester.request(selection)


class ResultsPresenter():

    def __init__(self, sublimePluginCommand):
        self.sublimePluginCommand = sublimePluginCommand

    def createWindowWithText(self, textToDisplay, fileType):
        newView = self.sublimePluginCommand.view.window().new_file()
        edit = newView.begin_edit()
        newView.insert(edit, 0, textToDisplay)
        newView.end_edit(edit)
        newView.set_scratch(True)
        newView.set_read_only(False)
        newView.set_name("http response")

        if fileType == HttpRequester.FILE_TYPE_HTML:
            newView.set_syntax_file("Packages/HTML/HTML.tmLanguage")
        if fileType == HttpRequester.FILE_TYPE_JSON:
            newView.set_syntax_file("Packages/JavaScript/JSON.tmLanguage")
        if fileType == HttpRequester.FILE_TYPE_XML:
            newView.set_syntax_file("Packages/XML/XML.tmLanguage")

        return newView.id()


class HttpRequesterCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global gPrevHttpRequest
        selection = ""
        for region in self.view.sel():
            # Concatenate selected regions together.
            selection += self.view.substr(region)

        gPrevHttpRequest = selection
        resultsPresenter = ResultsPresenter(self)
        httpRequester = HttpRequester(resultsPresenter)
        httpRequester.request(selection)

    def is_visible(self):

        is_visible = False

        # Only enable menu option if at least one region contains selected text.
        for region in self.view.sel():
            if not region.empty():
                is_visible = True

        return is_visible

    def is_enabled(self):
        return self.is_visible()
