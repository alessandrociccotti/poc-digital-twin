
# Gantt diagramm

```mermaid
gantt
    title Project Gantt
    dateFormat YYYY-MM-DD
    axisFormat %d/%m

    section Activities
    Research01 :p1, 2026-11-01, 7d
    Research02 :p1, 2026-11-01, 7d
    Delivery :p2, 2027-02-01, 7d
```

## List of activites

### Research

- define project scope and objectives;
- identify available real datasets;
- research existing components;
- define KPIs;

### Design

- define the three-station production line;
- define the overall PoC architecture;
- define simulation scenarios;

### Sprint 1

- implement the synthetic reference plant in SimPy;
- implement the digital twin with nominal configuration;
- implement telemetry generation and replay;
- verify simulation behaviour;
