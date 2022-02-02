# Python 3D Binaural Audio Simulation
![image_setup](images/audio3d.png?raw=true)

### Content
The program generates 3D Binaural sound for headphones produced by a number of loaded audio sources that can be moved with a GUI through a virtual 2 dimensional room. The sources can be for example instruments of a band that are mixed together to one 3D audio output that is saved as WAVE file. Kemar HRTFs are used for the filtering process. The platform independent port-audio library is used for audio playback.

### Architecture
The Gui Main Window Class provides the graphical user interface. The digital signal processing (DSP) algorithm can be stopped and paused through GUI Main Window by using a state object shared with the DSP instance, which is controlled by mutex access. The DSP class holds variables and methods which enable the binaural output. It holds one instance of the DspIn and DspOut class. The run() method of the DSP instance is called by GUI Main Window instance as Thread. It generates block by block a binaural audio output and sends it, after the set buffer size is reached, on a second thread to a playback queue which is then read by a PortAudio Callback Thread. To reach a higher computation performance the initialization function of the DspIn and DspOut instance performs time intensive calculations before starting the run() method. 

The steps of the DSP loop are:
1. Lock variables which are accessible through state class by gui and dsp algorithm
2. Set the common begin and end sample position in the speaker wave files input which needs to be read in this iteration.
3. Iterate over all speakers sp.
4. Read in current fitting hrtf for left and right ear and speaker block input
5. Convolve hrtfs with speaker block input using fft and overlap add
6. Mix binaural stereo blockoutput of every speaker to one binaural stereo block output having regard to speaker distances.
7. Add mixed binaural stereo block to play queue
8. Unlock shared variables.
9. Read play queue by PortAudio playback thread
10. If selected in GUI MainWindow: records the binaural output to a wave file
11. Finish DSP Algorithm, reset play and pause button

### Installation
You can install the package audio3d as following:

```python
conda create -n py34 python=3.4 -c conda-forge
activate py34
cd audio3d/src
python setup.py install
python audio3d
```

A documentation of all classes can be found in "sphinx_documentation/_build/html/index.html". Unit tests are given in "src/audio3d/".

### Authors
Felix Pfreundtner, Huaijiang Zhu, Manuela Heiss, Matthias Lederle
