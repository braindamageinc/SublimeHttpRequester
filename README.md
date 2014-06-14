***
# SublimeHttpRequester - HTTP client plugin for Sublime Text 2 & 3
***
====================

Contact: [braindamageinc@gmail.com](mailto:braindamageinc@gmail.com)

##Summary
Makes HTTP requests using the selected text as URL + headers. Useful for testing REST APIs from Sublime Text 2 editor. 

##Update: Added latency and download time output.

##Usage
Select the text that represents an URL. Examples of requests:

	http://www.google.com/search?q=test
	GET http://www.google.com/search?q=test
	www.google.com/search?q=test

If you need to add extra headers just add them below the URL line, one on each line:

	www.google.com/search?q=test
	Accept: text/plain
	Cookie : SOME_COOKIE

Use the right-click context menu command *Http Requester* or the keyboard shortcut *CTRL + ALT + R*  ( *COMMAND + ALT + R* on Mac OS X ).
Update: *F5* refreshes last request.

###POST/PUT usage
Just add **POST_BODY:** after any extra headers and the body on the following lines:

	POST http://posttestserver.com/post.php
	POST_BODY:
	this is the body that will be sent via HTTP POST
	a second line for body message

If you want to POST form variables:  

	POST http://posttestserver.com/post.php
	Content-type: application/x-www-form-urlencoded
	POST_BODY:
	variable1=avalue&variable2=1234&variable3=anothervalue

For PUT:

	PUT http://yoururl.com/puthere
	POST_BODY:
	this body will be sent via HTTP PUT

###DELETE usage
Same as HTTP GET:

	DELETE http://yoururl.com/deletethis

###Requesting through a proxy
If you need to send the request through a proxy server you can use:

	GET www.yourtest.com
	USE_PROXY: 127.0.0.1:1234

Where *127.0.0.1* is the proxy server address (IP or URL) followed by the port number. **Warning** : allways append a port number, even if it's *80*

###Using client SSL certificates
If you need client SSL certification you can use:

	GET https://yoursecureserver.com
	CLIENT_SSL_CERT: certif_file.pem
	CLIENT_SSL_KEY: key_file.key

###Using html charset
If you need to make a request for a page with a specific encoding such as cyrillic you can use:

	GET https://yoursecureserver.com
	CHARSET: cp1251

###Show results in the same results tab
If you wish to have all the requests responses in the same file (tab), you can use the following param:

	GET http://someserver.com
	SAME_FILE: True

###Set custom timeout
For a custom request timeout value, use the following param (timeout in **seconds**):

	GET http://someserver.com
	TIMEOUT: 5

	
## Installation
Using the Sublime Text 2/3 Package Control plugin (http://wbond.net/sublime_packages/package_control)
press *CTRL + SHIFT + P* and find **Package Control: Install Package** and press *Enter*.
Find this plugin in the list by name **Http Requester**.

Or git clone to your Sublime Text 2/3 packages folder directly (usually located at /Sublime Text 2/Packages/ or /Sublime Text 3/Packages/).
