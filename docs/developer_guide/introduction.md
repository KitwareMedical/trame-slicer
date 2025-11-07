# Introduction

## What is trame?

[Trame](https://www.kitware.com/trame/) is a Python-based framework that allows
creating Web applications entirely from Python. It boasts a rich list of
integrations including VTK, charts, maps and more.

Trame is compatible with local, remote, cloud, Jupyter and HPC deployment.

Under the hood, trame provides the server architecture, serves Vue3 application
to the Web client and handles server/client communication.

On the developer side, fully featured and modern applications can be created
with a few lines of Python code.

## What is trame-slicer?

Trame-slicer is a Python library bringing the 3D Slicer features to trame
developers. Its goal is _NOT_ to be a 3D Slicer replacement nor to be 3D Slicer
on the web but to bring 3D Slicer components to trame.

Trame-slicer relies on the 3D Slicer Python wrapping for core implementation and
bridges the gap to make them easily accessible in trame.

## Project structure

The project is organized with the following packages :

- core: Contains the main library components. Each component provide high level
  functionalities and are meant to be assembled at the application level.
  Components include the base application handling the core initialization as
  well as the Segmentation Editor and more.
- rca_views: Contains the glue between the views and trame's Remove Control Area
  component.
- resources: Contains static resources such as images and Volume rendering
  presets. Resource path can be overridden at the Slicer Application level if
  needed. This package can then be used as an example of content.
- segmentation: Contains all logic related to the segmentation and its effects
- utils: Contains utility functionalities not fitting the other main packages.
- views: Contains all classes related to the rendering logic.

## Using the library

trame-slicer is a library and provides different components to create medical
applications on the Web. As such, the library should not be forked when creating
applications but should be pip installed instead. The components can be
specialized and assembled as needed.

The examples folder provides an example of a medical viewer application. It will
be further refined in the future to provide more diverse examples and code
snippets on how to use the library for different use cases.
