/**
 * Comment Section - 일정 댓글 섹션 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { MessageCircle, Send, Trash2, Reply, Loader2, MessageSquare } from 'lucide-react';
import { getComments, createComment, deleteComment } from '../api/comments';
import type { ScheduleComment } from '../api/comments';
import { useAuth } from '../contexts/AuthContext';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface CommentSectionProps {
  scheduleId: number;
  onStartChat?: (userId: number, userName: string) => void;
}

const CommentSection: React.FC<CommentSectionProps> = ({ scheduleId, onStartChat }) => {
  const { user, isAuthenticated } = useAuth();
  const [comments, setComments] = useState<ScheduleComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState<{ id: number; userName: string } | null>(null);

  useEffect(() => {
    fetchComments();
  }, [scheduleId]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const data = await getComments(scheduleId);
      setComments(data);
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !isAuthenticated) return;

    setSubmitting(true);
    try {
      const comment = await createComment(scheduleId, {
        content: newComment.trim(),
        parent_id: replyTo?.id || null,
      });
      setComments([...comments, comment]);
      setNewComment('');
      setReplyTo(null);
    } catch (error) {
      console.error('댓글 작성 실패:', error);
      alert('댓글 작성에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: number) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return;

    try {
      await deleteComment(commentId);
      setComments(comments.map(c => 
        c.id === commentId 
          ? { ...c, is_deleted: true, content: '삭제된 댓글입니다' }
          : c
      ));
    } catch (error) {
      console.error('댓글 삭제 실패:', error);
      alert('댓글 삭제에 실패했습니다.');
    }
  };

  // 댓글을 트리 구조로 변환
  const buildCommentTree = () => {
    const rootComments = comments.filter(c => !c.parent_id);
    const replies = comments.filter(c => c.parent_id);

    return rootComments.map(root => ({
      ...root,
      replies: replies.filter(r => r.parent_id === root.id),
    }));
  };

  const commentTree = buildCommentTree();

  const CommentItem: React.FC<{ 
    comment: ScheduleComment & { replies?: ScheduleComment[] }; 
    isReply?: boolean;
  }> = ({ comment, isReply = false }) => (
    <div className={`${isReply ? 'ml-8 border-l-2 border-gray-200 dark:border-gray-700 pl-4' : ''}`}>
      <div className={`bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 ${comment.is_deleted ? 'opacity-60' : ''}`}>
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-bold text-sm">
              {comment.user_name[0].toUpperCase()}
            </div>
            <div>
              <button
                onClick={() => onStartChat?.(comment.user_id, comment.user_name)}
                className="font-semibold text-gray-900 dark:text-white hover:text-orange-600 dark:hover:text-orange-400 transition-colors"
                disabled={!onStartChat || comment.user_id === user?.id}
              >
                {comment.user_name}
              </button>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true, locale: ko })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {/* 채팅하기 버튼 */}
            {onStartChat && comment.user_id !== user?.id && !comment.is_deleted && (
              <button
                onClick={() => onStartChat(comment.user_id, comment.user_name)}
                className="p-1.5 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                title="채팅하기"
              >
                <MessageSquare size={16} className="text-blue-600 dark:text-blue-400" />
              </button>
            )}
            {/* 답글 버튼 */}
            {isAuthenticated && !comment.is_deleted && !isReply && (
              <button
                onClick={() => setReplyTo({ id: comment.id, userName: comment.user_name })}
                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                title="답글"
              >
                <Reply size={16} className="text-gray-600 dark:text-gray-400" />
              </button>
            )}
            {/* 삭제 버튼 */}
            {user?.id === comment.user_id && !comment.is_deleted && (
              <button
                onClick={() => handleDelete(comment.id)}
                className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                title="삭제"
              >
                <Trash2 size={16} className="text-red-600 dark:text-red-400" />
              </button>
            )}
          </div>
        </div>
        <p className={`text-gray-700 dark:text-gray-300 ${comment.is_deleted ? 'italic' : ''}`}>
          {comment.content}
        </p>
      </div>
      
      {/* 답글 렌더링 */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3 space-y-3">
          {comment.replies.map(reply => (
            <CommentItem key={reply.id} comment={reply} isReply />
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border-2 border-gray-100 dark:border-gray-700">
      <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-6 flex items-center gap-3">
        <MessageCircle className="text-blue-500" size={28} />
        댓글 ({comments.filter(c => !c.is_deleted).length})
      </h2>

      {/* 댓글 입력 폼 */}
      {isAuthenticated ? (
        <form onSubmit={handleSubmit} className="mb-6">
          {replyTo && (
            <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
              <Reply size={16} className="text-blue-600" />
              <span className="text-sm text-blue-700 dark:text-blue-300">
                {replyTo.userName}님에게 답글
              </span>
              <button
                type="button"
                onClick={() => setReplyTo(null)}
                className="ml-auto text-gray-500 hover:text-gray-700"
              >
                취소
              </button>
            </div>
          )}
          <div className="flex gap-3">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="댓글을 입력하세요..."
              className="flex-1 px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 transition-colors"
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              {submitting ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl text-center">
          <p className="text-gray-600 dark:text-gray-400">
            댓글을 작성하려면 <a href="/login" className="text-blue-600 hover:underline font-semibold">로그인</a>이 필요합니다.
          </p>
        </div>
      )}

      {/* 댓글 목록 */}
      {loading ? (
        <div className="text-center py-8">
          <Loader2 className="animate-spin mx-auto text-blue-500 mb-2" size={32} />
          <p className="text-gray-500">댓글 로딩 중...</p>
        </div>
      ) : commentTree.length === 0 ? (
        <div className="text-center py-12">
          <MessageCircle className="mx-auto text-gray-300 dark:text-gray-600 mb-4" size={48} />
          <p className="text-gray-500 dark:text-gray-400">아직 댓글이 없습니다. 첫 댓글을 남겨보세요!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {commentTree.map(comment => (
            <CommentItem key={comment.id} comment={comment} />
          ))}
        </div>
      )}
    </div>
  );
};

export default CommentSection;

