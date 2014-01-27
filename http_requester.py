import httplib
import sublime
import sublime_plugin
import socket
import types
import threading

gPrevHttpRequest = ""

CHECK_DOWNLOAD_THREAD_TIME_MS = 1000


def monitorDownloadThread(downloadThread):
    if downloadThread.is_alive():
        msg = downloadThread.getCurrentMessage()
        sublime.status_message(msg)
        sublime.set_timeout(lambda: monitorDownloadThread(downloadThread), CHECK_DOWNLOAD_THREAD_TIME_MS)
    else:
        downloadThread.showResultToPresenter()


class HttpRequester(threading.Thread):

    REQUEST_TYPE_GET = "GET"
    REQUEST_TYPE_POST = "POST"
    REQUEST_TYPE_DELETE = "DELETE"
    REQUEST_TYPE_PUT = "PUT"

    httpRequestTypes = [REQUEST_TYPE_GET, REQUEST_TYPE_POST, REQUEST_TYPE_PUT, REQUEST_TYPE_DELETE]

    HTTP_URL = "http://"
    HTTPS_URL = "https://"

    httpProtocolTypes = [HTTP_URL, HTTPS_URL]

    HTTP_POST_BODY_START = "POST_BODY:"

    HTTP_PROXY_HEADER = "USE_PROXY"

    HTTPS_SSL_CLIENT_CERT = "CLIENT_SSL_CERT"
    HTTPS_SSL_CLIENT_KEY = "CLIENT_SSL_KEY"

    CONTENT_LENGTH_HEADER = "Content-lenght"

    MAX_BYTES_BUFFER_SIZE = 8192

    FILE_TYPE_HTML = "html"
    FILE_TYPE_JSON = "json"
    FILE_TYPE_XML = "xml"

    HTML_CHARSET_HEADER = "CHARSET"
    htmlCharset = "utf-8"

    httpContentTypes = [FILE_TYPE_HTML, FILE_TYPE_JSON, FILE_TYPE_XML]

    HTML_SHOW_RESULTS_SAME_FILE_HEADER = "SAME_FILE"
    showResultInSameFile = False

    def __init__(self, resultsPresenter):
        self.totalBytesDownloaded = 0
        self.contentLenght = 0
        self.resultsPresenter = resultsPresenter
        threading.Thread.__init__(self)

    def request(self, selection):
        self.selection = selection
        self.start()
        sublime.set_timeout(lambda: monitorDownloadThread(self), CHECK_DOWNLOAD_THREAD_TIME_MS)

    def run(self):
        DEFAULT_TIMEOUT = 10
        FAKE_CURL_UA = "curl/7.21.0 (i486-pc-linux-gnu) libcurl/7.21.0 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.15 libssh2/1.2.6"

        selection = self.selection

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

        # get request headers from the lines below the http address
        (extra_headers, requestPOSTBody, proxyURL,  proxyPort, clientSSLCertificateFile,
         clientSSLKeyFile) = self.extractExtraHeaders(lines)

        headers = {"User-Agent": FAKE_CURL_UA, "Accept": "*/*"}

        for key in extra_headers:
            headers[key] = extra_headers[key]

        # if valid POST body add Content-lenght header
        if len(requestPOSTBody) > 0:
            headers[self.CONTENT_LENGTH_HEADER] = len(requestPOSTBody)
            requestPOSTBody = requestPOSTBody.encode('utf-8')


        for key in headers:
            print "REQ HEADERS ", key, " : ", headers[key]

        respText = ""
        fileType = ""

        useProxy = False
        if len(proxyURL) > 0:
            useProxy = True

        # make http request
        try:
            if not(useProxy):
                if httpProtocol == self.HTTP_URL:
                    conn = httplib.HTTPConnection(url, port, timeout=DEFAULT_TIMEOUT)
                else:
                    if len(clientSSLCertificateFile) > 0 or len(clientSSLKeyFile) > 0:
                        print "Using client SSL certificate: ", clientSSLCertificateFile
                        print "Using client SSL key file: ", clientSSLKeyFile
                        conn = httplib.HTTPSConnection(
                            url, port, timeout=DEFAULT_TIMEOUT, cert_file=clientSSLCertificateFile, key_file=clientSSLKeyFile)
                    else:
                        conn = httplib.HTTPSConnection(url, port, timeout=DEFAULT_TIMEOUT)

                conn.request(requestType, request_page, requestPOSTBody, headers)
            else:
                print "Using proxy: ", proxyURL + ":" + str(proxyPort)
                conn = httplib.HTTPConnection(proxyURL, proxyPort, timeout=DEFAULT_TIMEOUT)
                conn.request(requestType, httpProtocol + url + request_page, requestPOSTBody, headers)

            resp = conn.getresponse()
            (respText, fileType) = self.getParsedResponse(resp)
            conn.close()
        except (socket.error, httplib.HTTPException, socket.timeout) as e:
            if not(isinstance(e, types.NoneType)):
                respText = "Error connecting: " + str(e)
            else:
                respText = "Error connecting"
        except AttributeError as e:
            print e
            respText = "HTTPS not supported by your Python version"

        self.respText = respText
        self.fileType = fileType

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
            else:
                # may be proxy address URL:port
                if len(header_parts) > 2:
                    header_name = header_parts[0].rstrip()
                    header_value = header_parts[1]
                    header_value = header_value.lstrip()
                    header_value = header_value.rstrip()
                    for idx in range(2, len(header_parts)):
                        currentValue = header_parts[idx]
                        currentValue = currentValue.lstrip()
                        currentValue = currentValue.rstrip()
                        header_value = header_value + ":" + currentValue

                    return (header_name, header_value, readingPOSTBody)

        return (None, None, readingPOSTBody)

    def extractExtraHeaders(self, headerLines):
        requestPOSTBody = ""
        readingPOSTBody = False
        lastLine = False
        numLines = len(headerLines)

        proxyURL = ""
        proxyPort = 0

        clientSSLCertificateFile = ""
        clientSSLKeyFile = ""

        extra_headers = {}

        if len(headerLines) > 1:
            for i in range(1, numLines):
                lastLine = (i == numLines - 1)
                if not(readingPOSTBody):
                    (header_name, header_value, readingPOSTBody) = self.getHeaderNameAndValueFromLine(headerLines[i])
                    if header_name is not None:
                        if header_name == self.HTTP_PROXY_HEADER:
                            (proxyURL, proxyPort) = self.getProxyURLandPort(header_value)
                        elif header_name == self.HTTPS_SSL_CLIENT_CERT:
                            clientSSLCertificateFile = header_value
                        elif header_name == self.HTTPS_SSL_CLIENT_KEY:
                            clientSSLKeyFile = header_value
                        elif header_name == self.HTML_CHARSET_HEADER:
                            self.htmlCharset = header_value
                        elif header_name == self.HTML_SHOW_RESULTS_SAME_FILE_HEADER:
                            boolDict = {"true": True, "false": False}
                            self.showResultInSameFile = boolDict.get(header_value.lower())
                        else:
                            extra_headers[header_name] = header_value
                else:  # read all following lines as HTTP POST body
                    lineBreak = ""
                    if not(lastLine):
                        lineBreak = "\n"

                    requestPOSTBody = requestPOSTBody + headerLines[i] + lineBreak

        return (extra_headers, requestPOSTBody, proxyURL, proxyPort, clientSSLCertificateFile, clientSSLKeyFile)

    def getProxyURLandPort(self, proxyAddress):
        proxyURL = ""
        proxyPort = 0

        proxyParts = proxyAddress.split(":")

        proxyURL = proxyParts[0]

        if len(proxyParts) > 1:
            proxyURL = proxyParts[0]
            for idx in range(1, len(proxyParts) - 1):
                proxyURL = proxyURL + ":" + proxyParts[idx]

            lastIdx = len(proxyParts) - 1
            proxyPort = int(proxyParts[lastIdx])
        else:
            proxyPort = 80

        return (proxyURL, proxyPort)

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

        self.contentLenght = int(resp.getheader("content-length", 0))

        # download a 8KB buffer at a time
        respBody = resp.read(self.MAX_BYTES_BUFFER_SIZE)
        numDownloaded = len(respBody)
        self.totalBytesDownloaded = numDownloaded
        while numDownloaded == self.MAX_BYTES_BUFFER_SIZE:
            data = resp.read(self.MAX_BYTES_BUFFER_SIZE)
            respBody += data
            numDownloaded = len(data)
            self.totalBytesDownloaded += numDownloaded

        respText += respBody.decode(self.htmlCharset, "replace")

        return (respText, fileType)

    def getFileTypeFromContentType(self, contentType):
        fileType = self.FILE_TYPE_HTML
        contentType = contentType.lower()

        print "File type: ", contentType

        for cType in self.httpContentTypes:
            if cType in contentType:
                fileType = cType

        return fileType

    def getCurrentMessage(self):
        return "HttpRequester downloading " + str(self.totalBytesDownloaded) + " / " + str(self.contentLenght)

    def showResultToPresenter(self):
        self.resultsPresenter.createWindowWithText(self.respText, self.fileType, self.showResultInSameFile)


class HttpRequesterRefreshCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global gPrevHttpRequest
        selection = gPrevHttpRequest

        resultsPresenter = ResultsPresenter()
        httpRequester = HttpRequester(resultsPresenter)
        httpRequester.request(selection)


class ResultsPresenter():

    def __init__(self):
        pass

    def createWindowWithText(self, textToDisplay, fileType, showResultInSameFile):
        if not(showResultInSameFile):
            view = sublime.active_window().new_file()
            openedNewView = True
        else:
            view = self.findHttpResponseView()
            openedNewView = False
            if view is None:
                view = sublime.active_window().new_file()
                openedNewView = True

        edit = view.begin_edit()
        if not(openedNewView):
            view.insert(edit, 0, "\n\n\n")
        view.insert(edit, 0, textToDisplay)
        view.end_edit(edit)
        view.set_scratch(True)
        view.set_read_only(False)
        view.set_name("http response")

        if fileType == HttpRequester.FILE_TYPE_HTML:
            view.set_syntax_file("Packages/HTML/HTML.tmLanguage")
        if fileType == HttpRequester.FILE_TYPE_JSON:
            view.set_syntax_file("Packages/JavaScript/JSON.tmLanguage")
        if fileType == HttpRequester.FILE_TYPE_XML:
            view.set_syntax_file("Packages/XML/XML.tmLanguage")

        return view.id()

    def findHttpResponseView(self):
        for window in sublime.windows():
            for view in window.views():
                if view.name() == "http response":
                    return view

        return None


class HttpRequesterCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global gPrevHttpRequest
        selection = ""
        if self.has_selection():
            for region in self.view.sel():
                # Concatenate selected regions together.
                selection += self.view.substr(region)
        else:
            # Use entire document as selection
            entireDocument = sublime.Region(0, self.view.size())
            selection = self.view.substr(entireDocument)

        gPrevHttpRequest = selection
        resultsPresenter = ResultsPresenter()
        httpRequester = HttpRequester(resultsPresenter)
        httpRequester.request(selection)

    def has_selection(self):
        has_selection = False

        # Only enable menu option if at least one region contains selected text.
        for region in self.view.sel():
            if not region.empty():
                has_selection = True

        return has_selection
