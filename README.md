# Python 3D Binaural Audio Simulation
![image_setup](images/audio3d.png?raw=true)

### Content
The program generates 3D Binaural sound for headphones produced by a number of loaded audio sources that can be moved with a GUI through a virtual 2 dimensional room. The sources can be for example instruments of a band that are mixed together to one 3D audio output that is saved as WAVE file. Kemar HRTFs are used for the filtering process and the platform independent port-audio library is used for audio playback.

### Installation
You can install the package audio3d as following:

```python
conda create -n py34 python=3.4 -c conda-forge
activate py34
cd audio3d/src
python setup.py install
python audio3d
```
### Authors
Felix Pfreundtner, Huaijiang Zhu, Manuela Heiss, Matthias Lederle
