# The Quahl Web Browser ![](./quahl/browser/resources/icons/quahl/quahl_24.png)

*Quahl* (pronounded like the German word *Qual* [kva:l] 'torment') is a very simple,
customisable and embeddable, web browser based on Qt's QWebEngine wrapper around
the Chromium engine, written entirely in Python.

The main reason for making *Quahl* is to have a simple, customisable, controllable
and co-deployable web view component for Python app's using frameworks such as 
[Eel](https://github.com/python-eel/Eel).

While an *Eel*-App will work great with the application mode of Chromium, Chrome
or Edge, it is difficult to rely on the details of the user's installation of
that software (and some users may be reluctant to install a separate web browser
they might not otherwise use). This is where *Quahl* comes in, which can simply
be deployed as an included dependency of your Python app. You have full control
over the version of the Chromium engine/QtWebEngine version and can customise
the interface and settings as you may need. You also don't rely on the continued
offering of the `--app` switch on Chromium-based browsers in future.

**Note:** This is a very preliminary version, there's no guarantee anything works
well, that any bugs will be fixed, or that anything is stable (both in terms of
code/interfaces and execution!). Documentation will be forthcoming once some
other things have been sorted (and when/if I find the time).

## What Quahl is about

- A simple, usable Web Browser / WebView component
- Good integration / embedding with other Python apps
- Highly customizable and configurable
- Controllable from other processes via ICP over local TCP socket
- Cross-platform: Windows, MacOS, Linux
- A packagable alternative to Chromium's `--app` mode
- Free and open source

## What Quahl is not about

- A fully-featured Web Browser
- A thing for your daily web-browsing needs
- Tabbed browsing or advanced features
- Mobile platforms: not made for Android, iOS, etc.

## License

I haven't fully decided on the license for this yet, but it's available under the
*LGPL Version 3.0 or later* for now. If you have opinions or suggestions on why
something else might be better, feel free to let me know.

## Acknowledgments

The default icon set for Quahl is based on [Goran Spasojevic](https://github.com/gorango)'s
[Glyphs](https://glyphs.fyi/). For more on the icons see the [index of icons](https://html-preview.github.io/?url=https://github.com/thatfloflo/quahl/blob/main/quahl/browser/resources/icons/index_of_icons.html).

Some inspiration (but no code or resources) has been taken from Qt's [WebEngine Widgets Simple Browser Example](https://doc.qt.io/qt-6/qtwebengine-webenginewidgets-simplebrowser-example.html).