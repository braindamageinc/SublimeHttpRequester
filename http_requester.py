import webbrowser
import httplib
import sublime, sublime_plugin
import socket

class HttpRequesterCommand(sublime_plugin.TextCommand):

    REQUEST_TYPE_GET = "GET"
    REQUEST_TYPE_POST = "POST"
    REQUEST_TYPE_DELETE = "DELETE"
    REQUEST_TYPE_PUT = "PUT"

    httpRequestTypes = [REQUEST_TYPE_GET, REQUEST_TYPE_POST, REQUEST_TYPE_PUT, REQUEST_TYPE_DELETE]

    HTTP_URL = "http://"
    HTTPS_URL = "https://"

    httpProtocolTypes = [HTTP_URL, HTTPS_URL]

    def createWindowWithText(self, textToDisplay):
        newView = self.view.window().new_file()
        edit = newView.begin_edit()
        newView.insert(edit, 0, textToDisplay)
        newView.end_edit(edit)
        newView.set_scratch(True)
        newView.set_read_only(True)
        newView.set_name("http response")
        newView.set_syntax_file("Packages/HTML/HTML.tmLanguage")
        return newView.id()

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

        if len(url_parts) > url_idx+1:
            port = int(url_parts[url_idx+1]) 

        return (url, port, request_page, requestType, protocol)

    def extractExtraHeaders(self, headerLines):
        extra_headers = {}
        if len(headerLines) > 1:
            for i in range(1, len(headerLines)):
                line = headerLines[i]
                line = line.lstrip()
                line = line.rstrip()
                header_parts = line.split(":")
                if len(header_parts) == 2:
                    header_name = header_parts[0].rstrip()
                    header_value = header_parts[1].lstrip()
                    extra_headers[header_name] = header_value

        return extra_headers

    def getParsedResponse(self, resp):
        resp_status = "%d " % resp.status + resp.reason + "\n"
        respText = resp_status

        for header in resp.getheaders():
            respText += header[0] + ":" + header[1] + "\n"

        respText += "\n\n\n"
        respBody = resp.read()
        respText += respBody.decode("utf-8", "replace")

        return respText

    def run(self, edit):

        selection = ""
        for region in self.view.sel():
            # Concatenate selected regions together.
            selection += self.view.substr(region)

        DEFAULT_TIMEOUT = 10
        FAKE_CURL_UA = "curl/7.21.0 (i486-pc-linux-gnu) libcurl/7.21.0 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.15 libssh2/1.2.6"
        MY_UA = "python httpRequester 1.0.0"

        lines = selection.split("\n");

        # trim any whitespaces for all lines
        for idx in range(0, len(lines)):
            lines[idx] = lines[idx].lstrip()
            lines[idx] = lines[idx].rstrip()

        # get request web address and req. type from the first line
        (url, port, request_page, requestType, httpProtocol) = self.extractRequestParams(lines[0])

        print "Requesting...."
        print requestType, " ", httpProtocol, " HOST ", url, " PORT ", port ,  " PAGE: ", request_page

        #get request headers from the lines below the http address
        extra_headers = self.extractExtraHeaders(lines)

        headers = {"User-Agent": FAKE_CURL_UA, "Accept": "*/*"}

        for key in extra_headers:
            headers[key] = extra_headers[key]

        for key in headers:
            print "REQ HEADERS ", key, " : ", headers[key]
        
        # make http request
        try:
            if httpProtocol == self.HTTP_URL:
                conn = httplib.HTTPConnection(url, port, timeout = DEFAULT_TIMEOUT)
            else:
                conn = httplib.HTTPSConnection(url, port, timeout = DEFAULT_TIMEOUT)

            conn.request(requestType, request_page, "", headers)
            resp = conn.getresponse()
            respText = self.getParsedResponse(resp)
            conn.close()
        except (socket.error, httplib.HTTPException) as e:            
            respText = "Error connecting: " + e.strerror
        except AttributeError as e:
            print e
            respText = "HTTPS not supported by your Python version"

        self.createWindowWithText(respText)        
        
    def is_visible(self):

        is_visible = False

        # Only enable menu option if at least one region contains selected text.
        for region in self.view.sel():
            if not region.empty():
                is_visible = True

        return is_visible

    def is_enabled(self):
        return self.is_visible()