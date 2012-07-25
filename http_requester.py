import webbrowser
import httplib
import sublime, sublime_plugin

class HttpRequesterCommand(sublime_plugin.TextCommand):

    def createWindowWithText(self, textToDisplay):
        newView = self.view.window().new_file()
        edit = newView.begin_edit()
        newView.insert(edit, 0, textToDisplay)
        newView.end_edit(edit)
        newView.set_scratch(True)
        newView.set_read_only(True)
        newView.set_name("http response")
        newView.set_syntax_file("Packages/Diff/Diff.tmLanguage")
        return newView.id()

    def run(self, edit):

        selection = ""
        for region in self.view.sel():
            # Concatenate selected regions together.
            selection += self.view.substr(region)

        #http://www.google.ro

        DEFAULT_TIMEOUT = 10
        FAKE_CURL_UA = "curl/7.21.0 (i486-pc-linux-gnu) libcurl/7.21.0 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.15 libssh2/1.2.6"
        MY_UA = "python httpRequester 1.0.0"

        lines = selection.split("\n");

        # trim any whitespaces for all lines
        for idx in range(0, len(lines)):
            lines[idx] = lines[idx].lstrip()
            lines[idx] = lines[idx].rstrip()

        # get request web address
        webAddress = lines[0].replace("http://", "")
        request_parts = webAddress.split("/")
        request_page = "/"
        if len(request_parts) > 1:
            request_page = "/" + request_parts[1]        

        url_parts = request_parts[0].split(":")

        url_idx = 0
        if url_parts[0].find("http") != -1:
            url_idx = 1

        url = url_parts[url_idx]
        port = httplib.HTTP_PORT

        if len(url_parts) > url_idx+1:
            port = int(url_parts[url_idx+1]) 

        print "Requesting...."
        print "HOST ", url, " PORT ", port ,  " PAGE: ", request_page

        #get request headers
        extra_headers = {}
        if len(lines) > 1:
            for i in range(1, len(lines)):
                line = lines[i]
                line = line.lstrip()
                line = line.rstrip()
                header_parts = line.split(":")
                if len(header_parts) == 2:
                    header_name = header_parts[0].rstrip()
                    header_value = header_parts[1].lstrip()
                    extra_headers[header_name] = header_value

        headers = {"User-Agent": FAKE_CURL_UA, "Accept": "text/plain"}

        for key in extra_headers:
            headers[key] = extra_headers[key]

        for key in headers:
            print "REQ HEADERS ", key, " : ", headers[key]
        
        # make http request
        conn = httplib.HTTPConnection(url, port, timeout = DEFAULT_TIMEOUT)
        conn.request("GET", request_page, "", headers)
        resp = conn.getresponse()
        
        resp_status = "%d " % resp.status + resp.reason + "\n"
        respText = resp_status

        for header in resp.getheaders():
            respText += header[0] + ":" + header[1] + "\n"

        respText += "\n\n\n"

        respBody = resp.read()

        respText += respBody.decode("utf-8", "replace")

        conn.close()

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