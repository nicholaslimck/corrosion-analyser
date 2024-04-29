# corrosion-analyser
Analyse corroded pipelines and assess the integrity and remaining life as per [DNV-RP-F101](https://www.dnv.com/oilgas/download/dnv-rp-f101-corroded-pipelines.html).

Corrosion analyser is a web application that allows users to quickly analyse the integrity of corroded pipelines. The application is built using [Dash](https://dash.plotly.com/).

|                               Desktop Web UI                               |                              Mobile Web UI                               |
|:--------------------------------------------------------------------------:|:------------------------------------------------------------------------:|
| ![Alt text](/docs/CorrosionAnalyserDesktopInputWebUI.png "Desktop Web UI") | ![Alt text](/docs/CorrosionAnalyserMobileInputWebUI.png "Mobile Web UI") |

## Features
- Analyse corroded pipelines
- Assess the integrity and remaining life of corroded pipelines
- Graphically visualise computed results

![Alt text](/docs/CorrosionAnalyserOutputWebUI.png "Desktop Output Web UI")

## Usage
1. Input the pipeline details
2. Input the corrosion details
3. Click the "Calculate" button to get the results
4. The results will be displayed below the input form

## Deploy
The application can be accessed [here](https://corrosion-analyser.onrender.com/).

### Local Development
1. Clone the repository and navigate to the project directory
2. Install Python 3.11
3. Install [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
4. Install the dependencies using `poetry install`
5. Run the application using `poetry run python -m src.app`
6. Open the browser and navigate to [http://localhost:8050](http://localhost:8050)

### Run with Docker
```shell
docker run --name corrosion-analyser -p 8050:8050 nicholaslimck/corrosion-analyser
```

After the container is deployed, open the browser and navigate to [http://localhost:8050](http://localhost:8050)

### Run with Docker Compose
Download docker-compose.yml into your local machine:
```shell
curl https://raw.githubusercontent.com/nicholaslimck/corrosion-analyser/main/docker-compose.yml > docker-compose.yml
```

Run the app using docker compose:
```shell
docker compose up
```

After the container is deployed, open the browser and navigate to [http://localhost:8050](http://localhost:8050)

## Project Structure
### Logic Flow
```mermaid
---
title: Logic Flow
---
flowchart 
    subgraph Frontend
        A[Input Parameters] --> B[Click on Analyse]
        K
        L
    end
    subgraph Backend
        B --> C[Validate Inputs]
        C --Inputs Validated--> D
        C --Inputs Invalid--> L[Display Error]
        subgraph Processing
        D(Prepare all inputs) --> E1(Create Pipe)
        D --> E2(Create Defect) --> E1
        D --> E3(Create Environment) --> E1
        D --> E4(Create Loading) --> E1
        E1 --> F(Calculate Pressure Resistance\nCalculate Effective Pressure)
        F --> G(Calculate Maximum Allowable Defect Depth)
        G -- Time-Shifted Defect Data Provided --> H(Calculate Corrosion Rate\nEstimate Remaining Life)
        end
        subgraph Generate Output
            G -- Time-Shifted Defect Data Not Provided --> I(Generate Plots)
            H --> I(Generate Plots)
            I --> J(Generate Results)
        end
    end
    J --> K[Display Results]
```
### Class Structure
```mermaid
---
title: Example Pipe
---
classDiagram
    class Pipe{
        +dict config
        +Defect defect
        +Environment environment
        +Loading loading
        +Properties properties
        +PipeDimensions pipe_dimensions
        +MaterialProperties material_properties
        +DesignLimits design_limits
        +Factors factors
        +add_defect(defect: Defect)
        +add_loading(axial_load: float, bending_load: float, combined_stress: float)
        +set_environment(environment: Environment)
        +calculate_pressure_resistance()
        +calculate_effective_pressure()
        +calculate_maximum_allowable_defect_depth()
        +estimate_remaining_life()
        +calculate_corrosion_rate()
        
    }
    class Defect{
        +float length
        +float width
        +float depth
        +float relative_depth
        +float relative_depth_with_uncertainty
        +float length_correction_factor
        +float pressure_resistance
        +float measurement_timestamp
        +float position
    }
    Pipe <-- Defect
    class PipeDimensions{
        +float outside_diameter
        +float wall_thickness
    }
    PipeDimensions --> Pipe
    class MaterialProperties{
        +float alpha_u
        +float temperature
        +float smts
        +float smys
        +float f_u_temp
        +float f_y_temp
    }
    MaterialProperties --> Pipe
    class DesignLimits{
        +float design_pressure
        +float design_temperature
        +float incidental_to_design_pressure_ratio
    }
    Pipe <-- DesignLimits
    class Environment{
        +float seawater_density
        +float containment_density
        +float elevation_reference
        +float elevation
        +float external_pressure
        +float incidental_pressure
    }
    Pipe <-- Environment
    class Loading{
        +float usage_factor
        +float axial_stress
        +float bending_stress
        +float loading_stress
    }
    Loading --> Pipe
    class Properties{
        +float pressure_resistance
        +float effective_pressure
        +DataFrame maximum_allowable_defect_depth
        +float remaining_life
    }
    Properties --> Pipe
    class Factors{
        +str safety_class
        +str inspection_method
        +float measurement_accuracy
        +float confidence_level
        +float wall_thickness
        +float standard_deviation
        +float gamma_m
        +float gamma_d
        +float epsilon_d
        +float xi
    }
    Factors --> Pipe
    Factors --> Defect
    
```