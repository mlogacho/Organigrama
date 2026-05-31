from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    title: str = ""


class Edge(BaseModel):
    from_id: str = Field(..., alias="from", min_length=1)
    to_id: str = Field(..., alias="to", min_length=1)
    label: str = ""

    class Config:
        populate_by_name = True


class OrgChart(BaseModel):
    nodes: list[Node]
    edges: list[Edge]


class TranscriptionResponse(BaseModel):
    transcript: str
    org_chart: OrgChart
