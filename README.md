# EntitySelect

A [Sublime Text 3](http://www.sublimetext.com/) package providing a unified 
framework for executing code based on the current selection.

This package provides no functionality on its own. Instead, it is intended to 
be extended by package developers.

When this document refers to entities, it is referring to a logical grouping 
of characters within the document. For example, the name of a class, method,
or variable is an entity. 

## Features

*   Write classes to perform actions and interact with the currently selected
    entity.
*   This package includes three basic methods for interacting with entities:
    *   DocLink: If the current entity supports DocLink, it will be underlined 
        when selected to indicate there is additional information available 
        for the entity. Pressing Alt+d will open that additional information.
        You can also optionally add functionality to add documentation.
    *   Status Identifier: If the current entity supports Status Identifier, 
        an informational note will be displayed in the footer bar when that 
        entity is selected.
    *   Highlighting: If the current entity supports Highlighting, you can 
        invoke it to highlight all instances of that entity within the current 
        file, function, class, etc. You can then navigate between the 
        instances of the entity or select them all. This operates like a quick
        find for specific entities.

These basic methods can be extended to add complex IDE-like functionality to 
Sublime Text.

# Installation

## Package Control

Install [Package Control](http://wbond.net/sublime_packages/package_control). Add this repository (https://bitbucket.org/kbaskett/entityselect) to Package Control. EntitySelect will show up in the packages list.

## Manual installation

Go to the "Packages" directory (`Preferences` > `Browse Packages…`). Then download or clone this repository:

https://bitbucket.org/kbaskett/entityselect.git

# Default Keybindings
These commands are also available in the Context Menu:
  
*   Alt+D - Invoke DocLink if the current entity supports it. Additional 
    information for the entity will be opened.
*   Alt+H - Invoke Highlight if the current entity supports it. All instances 
    of the entity will be highlighted.
*   Alt+J - Move to the next highlighted instance.
*   Alt+K - Move to the previous highlighted instance.
*   Alt+L - Select all highlighted instances.
*   Alt+Shift+L - Display a quick panel showing all highlighted instances.
*   Esc - Clear highlights if they are visible.

