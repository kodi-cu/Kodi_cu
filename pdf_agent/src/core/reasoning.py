"""Sistema de razonamiento del agente"""
import re
from typing import List, Dict
from dataclasses import dataclass
from colorama import Fore, Style

@dataclass
class ReasoningSection:
    type: str
    content: str
    label: str
    color: str

class ReasoningEngine:
    PATTERNS = [
        (r"<reasoning>(.*?)</reasoning>", "reasoning", "RAZONAMIENTO", Fore.CYAN),
        (r"<thinking>(.*?)</thinking>", "thinking", "PENSAMIENTO", Fore.CYAN),
    ]
    
    def parse(self, text: str) -> List[ReasoningSection]:
        sections = []
        for pattern, ptype, label, color in self.PATTERNS:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                sections.append(ReasoningSection(ptype, match.strip(), label, color))
        return sections
