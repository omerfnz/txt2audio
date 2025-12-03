import { Plus, BookOpen, Sparkles, Clock, CheckCircle, AlertCircle, Loader2, Trash2, Merge } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getAllProjects, deleteProject } from '../api/client';
import { clsx } from 'clsx';
import { AlertDialog } from './AlertDialog';

interface Project {
    id: number;
    name: string;
    status: string;
    created_at: string | null;
    audio_path?: string | null;
}

interface SidebarProps {
    onNewProject: () => void;
    onProjectClick?: (projectId: number) => void;
    currentProjectId?: number | null;
}

export function Sidebar({ onNewProject, onProjectClick, currentProjectId }: SidebarProps) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; projectId: number | null; projectName: string }>({
        isOpen: false,
        projectId: null,
        projectName: ''
    });

    useEffect(() => {
        loadProjects();
        const interval = setInterval(loadProjects, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadProjects = async () => {
        try {
            const data = await getAllProjects();
            setProjects(data.projects);
        } catch (error) {
            console.error('Failed to load projects:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteClick = (projectId: number, projectName: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setDeleteDialog({
            isOpen: true,
            projectId,
            projectName
        });
    };

    const handleDeleteConfirm = async () => {
        if (!deleteDialog.projectId) return;

        try {
            await deleteProject(deleteDialog.projectId);
            await loadProjects();
            setDeleteDialog({ isOpen: false, projectId: null, projectName: '' });
        } catch (error) {
            console.error('Failed to delete project:', error);
            alert('Failed to delete project');
        }
    };

    const handleDeleteCancel = () => {
        setDeleteDialog({ isOpen: false, projectId: null, projectName: '' });
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return 'Unknown';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const getStatusIcon = (status: string, audioPath: string | null | undefined) => {
        if (status === 'completed' && !audioPath) {
            return <Merge className="w-4 h-4 text-purple-500 animate-pulse" />;
        }

        switch (status) {
            case 'merging':
                return <Merge className="w-4 h-4 text-purple-500 animate-pulse" />;
            case 'completed':
                return <CheckCircle className="w-4 h-4 text-emerald-500" />;
            case 'processing':
                return <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />;
            case 'failed':
                return <AlertCircle className="w-4 h-4 text-red-500" />;
            default:
                return <Clock className="w-4 h-4 text-slate-500" />;
        }
    };

    const getStatusColor = (status: string, audioPath: string | null | undefined) => {
        if (status === 'completed' && !audioPath) {
            return 'text-purple-400';
        }

        switch (status) {
            case 'merging':
                return 'text-purple-400';
            case 'completed':
                return 'text-emerald-400';
            case 'processing':
                return 'text-indigo-400';
            case 'failed':
                return 'text-red-400';
            default:
                return 'text-slate-400';
        }
    };

    const getStatusText = (status: string, audioPath: string | null | undefined) => {
        if (status === 'completed' && !audioPath) {
            return 'merging';
        }
        return status;
    };

    return (
        <div className="w-80 h-screen glass border-r border-white/10 flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex-shrink-0">
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
            <div className="p-4 flex-shrink-0">
                <button
                    onClick={onNewProject}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all duration-300 font-medium shadow-lg hover:shadow-indigo-500/50 group"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
                    <span>New Project</span>
                </button>
            </div>

            {/* Projects Section - INLINE STYLE FIX */}
            <div
                className="px-4 pb-4"
                style={{
                    flex: '1 1 0%',
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: 0,
                    overflow: 'hidden'
                }}
            >
                {/* Section Header - FIXED */}
                <div className="flex-shrink-0 mb-3">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Sparkles className="w-3 h-3" />
                        <span>Recent Projects</span>
                        {projects.length > 0 && (
                            <span className="ml-auto text-slate-500">({projects.length})</span>
                        )}
                    </h2>
                </div>

                {/* Projects List - SCROLLABLE! */}
                <div
                    className="pr-2"
                    style={{
                        flex: '1 1 0%',
                        minHeight: 0,
                        overflowY: 'scroll',
                        overflowX: 'hidden',
                        scrollbarWidth: 'thin',
                        scrollbarColor: 'rgba(99, 102, 241, 0.6) rgba(15, 23, 42, 0.5)'
                    }}
                >
                    <div className="space-y-2">
                        {loading ? (
                            <div className="text-sm text-slate-400 text-center py-8 flex items-center justify-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Loading...</span>
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="text-sm text-slate-400 text-center py-8 animate-pulse-soft">
                                No projects yet.
                            </div>
                        ) : (
                            projects.map((project) => (
                                <div
                                    key={project.id}
                                    onClick={() => onProjectClick?.(project.id)}
                                    className={clsx(
                                        'p-3 rounded-xl cursor-pointer transition-all duration-200 border group',
                                        currentProjectId === project.id
                                            ? 'bg-indigo-500/20 border-indigo-500/50'
                                            : 'hover:bg-white/5 border-transparent hover:border-indigo-500/30'
                                    )}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                {getStatusIcon(project.status, project.audio_path)}
                                                <p className="text-sm font-medium text-slate-200 truncate">
                                                    {project.name}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2 text-xs">
                                                <span className={clsx('capitalize', getStatusColor(project.status, project.audio_path))}>
                                                    {getStatusText(project.status, project.audio_path)}
                                                </span>
                                                <span className="text-slate-500">•</span>
                                                <span className="text-slate-500">
                                                    {formatDate(project.created_at)}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 flex-shrink-0">
                                            <span className="text-xs text-slate-500">#{project.id}</span>
                                            <button
                                                onClick={(e) => handleDeleteClick(project.id, project.name, e)}
                                                className="p-1.5 hover:bg-red-500/20 rounded-lg text-slate-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                                title="Delete project"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Delete Confirmation Dialog */}
            <AlertDialog
                isOpen={deleteDialog.isOpen}
                title="Delete Project"
                message={`Are you sure you want to delete "${deleteDialog.projectName}"? This action cannot be undone.`}
                confirmText="Delete"
                cancelText="Cancel"
                onConfirm={handleDeleteConfirm}
                onCancel={handleDeleteCancel}
                variant="danger"
            />
        </div>
    );
}
