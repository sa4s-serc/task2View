# Request (ISO/IEC/IEEE 42010 inputs)
- **Stakeholder:** DevOps engineer
- **Perspective:** the Kubernetes deployment shipped in the repo (`k8s/`)
- **Concern:** what runs where in the cluster, how is it reached, and how does the app get its database?
- **Concern details:** (1) runtime nodes and the images deployed on them; (2) how clients reach the app (ports, Service type); (3) app-to-database connection and credentials; (4) health checks.
- **Viewpoint:** deployment
- **Model kind:** UML deployment diagram
- **Subject:** spring-projects/spring-petclinic @ 500158f
