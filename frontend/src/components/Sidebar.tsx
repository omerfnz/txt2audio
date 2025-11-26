import { Plus, BookOpen, Sparkles } from 'lucide-react';

interface Project {
    id: number;
    name: string;
    status: string;
}

interface SidebarProps {
    projects?: Project[];
    onNewProject: () => void;
}

export function Sidebar({ projects = [], onNewProject }: SidebarProps) {
    return (
        <div className={`w-80 h-full glass border-r border-white/10 flex flex-col transition-all duration-300 lg:w-80 lg:block hidden md:flex`}>
            {/* Header */}
            <div className="p-6 border-b border-white/10">
                <div className="flex items-center justify-between">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-2">
                        <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl glow">
                            <BookOpen className="w-5 h-5 text-white" />
                        </div>
                        <span>AudioStudio</span>
                    </h1>
                </div>
            </div>

            {/* New Project Button */}
            <div className="p-4">
                <button
                    onClick={onNewProject}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all duration-300 font-medium shadow-lg hover:shadow-indigo-500/50 group"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
                    <span>New Project</span>
                </button>
            </div>

            {/* Projects List */}
            <div className="flex-1 overflow-y-auto p-4 pt-0">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Sparkles className="w-3 h-3" />
                    <span>Recent Projects</span>
                </h2>
                <div className="space-y-2">
                    {projects.length === 0 ? (
                        <div className="text-sm text-slate-400 text-center py-8 animate-pulse-soft">
                            No projects yet.
                        </div>
                    ) : (
                        projects.map((_project, idx) => (
                            <div
                                key={idx}
                                className="p-3 rounded-xl hover:bg-white/5 cursor-pointer text-sm text-slate-200 transition-all duration-200 border border-transparent hover:border-indigo-500/30 group"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-indigo-500 group-hover:animate-pulse" />
                                    <span>Project {idx + 1}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
