import { Plus, BookOpen, Sparkles, Clock, CheckCircle, AlertCircle, Loader2, Trash2, Merge } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getAllProjects, deleteProject } from '../api/client';
import { cn } from '@/lib/utils';
import { AlertDialog } from './AlertDialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

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
        <div className="w-80 h-screen bg-card border-r border-border flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-border flex-shrink-0">
                <div className="flex items-center justify-between">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-primary bg-clip-text text-transparent flex items-center gap-2">
                        <div className="p-2 bg-primary rounded-xl">
                            <BookOpen className="w-5 h-5 text-primary-foreground" />
                        </div>
                        <span>AudioStudio</span>
                    </h1>
                </div>
            </div>

            {/* New Project Button */}
            <div className="p-4 flex-shrink-0">
                <Button
                    onClick={onNewProject}
                    className="w-full flex items-center justify-center gap-2 group"
                    size="lg"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
                    <span>New Project</span>
                </Button>
            </div>

            {/* Projects Section */}
            <div className="flex-1 flex flex-col min-h-0 px-4 pb-4">
                {/* Section Header */}
                <div className="flex-shrink-0 mb-3">
                    <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                        <Sparkles className="w-3 h-3" />
                        <span>Recent Projects</span>
                        {projects.length > 0 && (
                            <Badge variant="secondary" className="ml-auto">
                                {projects.length}
                            </Badge>
                        )}
                    </h2>
                </div>

                {/* Projects List - SCROLLABLE! */}
                <ScrollArea className="flex-1">
                    <div className="space-y-2 pr-4">
                        {loading ? (
                            <div className="text-sm text-muted-foreground text-center py-8 flex items-center justify-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Loading...</span>
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="text-sm text-muted-foreground text-center py-8">
                                No projects yet.
                            </div>
                        ) : (
                            projects.map((project) => (
                                <Card
                                    key={project.id}
                                    onClick={() => onProjectClick?.(project.id)}
                                    className={cn(
                                        'p-3 cursor-pointer transition-all duration-200 group',
                                        currentProjectId === project.id
                                            ? 'bg-primary/10 border-primary'
                                            : 'hover:bg-accent/50'
                                    )}
                                >
                                    <div className="flex items-center justify-between gap-2 w-full overflow-hidden">
                                        <div className="flex-1 min-w-0 flex flex-col gap-1">
                                            <div className="flex items-center gap-2 w-full">
                                                <div className="shrink-0">
                                                    {getStatusIcon(project.status, project.audio_path)}
                                                </div>
                                                <p className="text-sm font-medium text-foreground truncate flex-1 min-w-0" title={project.name}>
                                                    {project.name}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2 text-xs">
                                                <Badge variant="outline" className={cn('capitalize text-xs shrink-0', getStatusColor(project.status, project.audio_path))}>
                                                    {getStatusText(project.status, project.audio_path)}
                                                </Badge>
                                                <span className="text-muted-foreground shrink-0">•</span>
                                                <span className="text-muted-foreground truncate">
                                                    {formatDate(project.created_at)}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0 pl-1">
                                            <span className="text-xs text-muted-foreground">#{project.id}</span>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={(e) => handleDeleteClick(project.id, project.name, e)}
                                                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                title="Delete project"
                                            >
                                                <Trash2 className="w-4 h-4 text-destructive" />
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            ))
                        )}
                    </div>
                </ScrollArea>
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
