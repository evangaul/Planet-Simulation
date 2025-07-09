# Planetary Simulation
A 2D simulation of the solar system built with Python and Pygame. Planets orbit the Sun with realistic elliptical paths based on astronomical data. 

# Features
- Planets follow a realistic elliptical orbit path using semi-major axes and eccentricities from NASA data.
- Camera Controls, pan with arrow keys or mouse drag and zoom in/out with 'z'
- Planet names and distances show when hovering near a planet
- Trails show the path of the planet

# Notes
- The simulation uses a simplified 2D model with coplanar orbits.
- The Euler integration method could have small errors over long periods. Maybe consider Verlet or Runge-Kutta for better accuracy.
- Scale factors might need an adjustment to view all planets (Pluto is far away)
