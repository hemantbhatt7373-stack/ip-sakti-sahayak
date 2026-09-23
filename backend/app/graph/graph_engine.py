import json
import os
import networkx as nx

class KnowledgeGraphEngine:
    def __init__(self, data_path: str = "backend/data/knowledge_base.json"):
        self.graph = nx.MultiDiGraph()
        self.data_path = data_path
        self._build_graph()

    def _build_graph(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Knowledge base not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Add Legal Nodes
        for section in data.get("legal_sections", []):
            sec_id = f"{section['act']} - Sec {section['section']}"
            self.graph.add_node(
                sec_id,
                type="LegalSection",
                title=section["title"],
                rule=section["rule"],
                guidance=section["guidance"]
            )

        # 2. Add Herbal Nodes and Relations
        for herb in data.get("herbal_knowledge", []):
            herb_id = herb["herb"]
            self.graph.add_node(
                herb_id,
                type="Herb",
                botanical=herb["botanical_name"],
                scope=herb["patentable_scope"]
            )

            # Link Classical Texts
            for text in herb["classical_texts"]:
                self.graph.add_node(text, type="ClassicalText")
                self.graph.add_edge(herb_id, text, relation="MENTIONED_IN")

            # Link Properties
            for prop in herb["traditional_properties"]:
                self.graph.add_node(prop, type="Property")
                self.graph.add_edge(herb_id, prop, relation="HAS_PROPERTY")

            # Link to Patent Act 3(p) and NBA Sec 6
            self.graph.add_edge(herb_id, "The Patents Act, 1970 - Sec 3(p)", relation="GOVERNED_BY")
            self.graph.add_edge(herb_id, "Biological Diversity Act, 2002 - Sec 6", relation="REQUIRES_COMPLIANCE")

    def inspect_herb(self, herb_name: str):
        """Query herb details and compliance rules directly from graph"""
        matches = [n for n in self.graph.nodes if herb_name.lower() in n.lower()]
        if not matches:
            return None

        target = matches[0]
        neighbors = self.graph.adj[target]
        
        info = {
            "node": target,
            "data": self.graph.nodes[target],
            "related_texts": [],
            "properties": [],
            "legal_mandates": []
        }

        for nbr, edges in neighbors.items():
            for _, edge_data in edges.items():
                rel = edge_data["relation"]
                if rel == "MENTIONED_IN":
                    info["related_texts"].append(nbr)
                elif rel == "HAS_PROPERTY":
                    info["properties"].append(nbr)
                elif rel in ["GOVERNED_BY", "REQUIRES_COMPLIANCE"]:
                    sec_data = self.graph.nodes[nbr]
                    info["legal_mandates"].append({
                        "section": nbr,
                        "title": sec_data.get("title"),
                        "guidance": sec_data.get("guidance")
                    })

        return info


# Quick Verification run
if __name__ == "__main__":
    engine = KnowledgeGraphEngine()
    result = engine.inspect_herb("हल्दी")
    print(json.dumps(result, ensure_ascii=False, indent=2))