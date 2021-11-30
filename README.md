![image_setup](images/audio3d.png?raw=true)

Python 3D Binaural Audio Simulation

The program generates 3D Binaural sound for headphones produced by a number of loaded audio sources that can be moved by a GUI through a virtual 2 dimensional room. The sources can be for example instruments of a band that are mixed together to one 3D audio output that is saved as WAVE file. Kemar HRTFs were used for the filtering process.

You can install the package audio3d as following:

```python
conda create -n py34 python=3.4 -c conda-forge
activate py34
cd audio3d/src
python setup.py install
python audio3d
```