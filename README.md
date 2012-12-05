***
# SublimeHttpRequester - HTTP client plugin for Sublime Text 2
***
====================

Contact: [braindamageinc@gmail.com](mailto:braindamageinc@gmail.com)

##Summary
Makes HTTP requests using the selected text as URL + headers. Usefull for testing REST APIs from Sublime Text 2 editor. 

##Update: GET/PUT/POST/DELETE supported

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
	
## Installation
Using the Sublime Text 2 Package Control plugin (http://wbond.net/sublime_packages/package_control)
press *CTRL + SHIFT + P* and find **Package Control: Install Package** and press *Enter*.
Find this plugin in the list by name **Http Requester**.

Or git clone to your Sublime Text 2 packages folder directly (usually located at /Sublime Text 2/Packages/).
