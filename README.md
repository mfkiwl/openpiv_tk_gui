# Simple GUI for Open PIV

This graphical user interface provides an efficient workflow for evaluating and postprocessing particle image velocimetry (PIV) images. OpenPivGui relies on the python libraries provided by the [OpenPiv project](http://www.openpiv.net/).

![Screen shot of the GUI showing a vector plot and corresponding parameters.](./fig/open_piv_gui_vector_plot.png)

## Installation

You may use Pip to install `OpenPivGui`:

```
pip3 install openpivgui
```

## Launching

Launch `OpenPivGui` by executing:

```
python3 -m openpivgui.OpenPivGui
```
## Launch without installation

Alternatively, just clone this repository or manually copy the directory `openpivgui` to your local computer, cd into that directory, and execute `python3 OpenPivGui.py`.

## Using and Extending the GUI

### Introduction Video

Watch a ten minute video to learn how to use and extend OpenPivGui:

https://video.fh-muenster.de/Panopto/Pages/Viewer.aspx?id=309dccc2-af58-44e0-8cd3-ab9500c5b7f4

### Usage

1. Press »select files for processing« and choose some images. Use Ctrl + Shift for selecting mutliple files.
2. To inspect the images, click on the links in the file-list on the right.
3. Walk through the tabs, select the desired functions, and edit the corresponding parameters.
4. Press »start processing chain« to start the evaluation.
5. Inspect the results by clicking on the links in the file-list.
6. Use the »back« and »forward« buttons to inspect intermediate results.
4. Use »dump settings« to document your project. You can recall them anytime by pressing »load settings«. The lab-book entries are also restored from the settings file.

### Extension

Extending the GUI, usually comprises two tasks:

1. Adding new variables and a corresponding widgets to enable users to modify its values.
2. Adding a new function or method.

#### Adding new variables

Open the script `OpenPivParams.py`. Find the method `__init__()`. There, you find a variable, called `default` of type dict. All widgets like checkboxes, text entries, and option menues are created based on the content of this dictionary. 

By adding a dictionary element, you add a variable. A corresponding widget is automatically created. Example:

```
'corr_window':             # key
    [3020,                 # index
	'int',                # type
	32,                   # value
	(8, 16, 32, 64, 128), # hints
    'window size',        # label
    'Size in pixel.'],    # help
```

In `OpenPivGui.py` you access the value of this variable via `p['corr_window']`. Here, `p` is the instance name of an `OpenPivParams` object. Typing

```
print(p.['corr_window'])
```

will thus result in:

```
32
```
The other fields are used for widget creation:

- index: An index of 3xxx will place the widget on the third rider (»PIV«).
- type:
    + `None`: Creates a new notebook rider.
	+ `boolean`: A checkbox will be created.
	+ `str[]`: Creates a listbox.
	+ `text`: Provides a text area.
	+ `float`, `int`, `str`: An entry widget will be created.
- hints: If hints is not `None`, an option menu is provided with `hints` as options.
- label: The label next to the manipulation widget.
- help: The content of this field will pop up as a tooltip, when the mouse is moved over the widget.

#### Adding a new method

Open the script `OpenPivGui`. There are two main possibilities, of doing something with the newly created variables:

1. Extend the existing processing chain.

2. Creating a new method.

##### Extend existing processing chain

Find the function definition `start_processing()`. Add another `if` statement and some useful code.

##### Create a new method

Find the function definition `__init_buttons()`. Add something like:

```
ttk.Button(f,
           text='button label',
           command=self.new_func).pack(fill='x')
```
Add the new function:

```
def new_func(self):
    # do something useful here
    pass
```