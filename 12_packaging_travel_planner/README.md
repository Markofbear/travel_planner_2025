# Creating python package

As we've noticed, using python scripts and importing other modules from sibling directories is not a simple task to do in a clean way. There are several ways to solve this:

- :x: using sys.path and append a path for Python to look for. I don't recommend doing this as it is not a clean solution and may cause problems down the road with maintainability making the code unpredictable
- :x: adding to a PYTHONPATH variable, this is also not recommended in general due to portability issues
- :white_check_mark: in docker container PYTHONPATH can be used 
- :white_check_mark: creating a package that you can install - do this

<a href="https://youtu.be/3_ZZ80Symjc" target="_blank">
  <img src="https://github.com/kokchun/assets/blob/main/python_videos/packaging.png?raw=true" alt="course structure" width="600">
</a>
