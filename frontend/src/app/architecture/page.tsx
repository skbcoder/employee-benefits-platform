"use client";

import { useState } from "react";
import DeploymentTab from "./components/DeploymentTab";
import OrchestrationTab from "./components/OrchestrationTab";
import AgenticTab from "./components/AgenticTab";
import DataTab from "./components/DataTab";
import CloudTab from "./components/CloudTab";

type Tab = "diagram" | "orchestration" | "agentic" | "data" | "cloud";

const TABS: { id: Tab; label: string }[] = [
  { id: "diagram", label: "Deployment" },
  { id: "orchestration", label: "Orchestration" },
  { id: "agentic", label: "Agentic AI" },
  { id: "data", label: "Data & Schemas" },
  { id: "cloud", label: "Cloud Evolution" },
];

export default function ArchitecturePage() {
  const [activeTab, setActiveTab] = useState<Tab>("diagram");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">System Architecture</h1>
        <p className="mt-1 text-sm text-gray-400">
          Employee Benefits Platform — interactive deployment diagram, architecture details, performance analysis, and cloud evolution roadmap.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#0d0d14] p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-md px-3 py-2 text-xs font-medium transition ${
              activeTab === tab.id
                ? "bg-gray-800 text-gray-100"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "diagram" && <DeploymentTab />}
      {activeTab === "orchestration" && <OrchestrationTab />}
      {activeTab === "agentic" && <AgenticTab />}
      {activeTab === "data" && <DataTab />}
      {activeTab === "cloud" && <CloudTab />}

      {/* Footer */}
      <div className="border-t border-gray-800 pt-4 text-center text-xs text-gray-600">
        Employee Benefits Platform · 11 services · 6 DB schemas · 3 Flyway migrations · Outbox/Inbox messaging · Multi-agent AI orchestration
      </div>
    </div>
  );
}
