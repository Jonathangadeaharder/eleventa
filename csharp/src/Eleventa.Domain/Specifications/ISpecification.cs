using System.Linq.Expressions;

namespace Eleventa.Domain.Specifications;

/// <summary>
/// Specification pattern interface.
/// Encapsulates business rules for querying and filtering.
/// </summary>
public interface ISpecification<T>
{
    /// <summary>
    /// Checks if the entity satisfies the specification.
    /// </summary>
    bool IsSatisfiedBy(T entity);

    /// <summary>
    /// Gets the expression tree for LINQ queries.
    /// </summary>
    Expression<Func<T, bool>> ToExpression();

    /// <summary>
    /// Combines this specification with another using AND logic.
    /// </summary>
    ISpecification<T> And(ISpecification<T> other);

    /// <summary>
    /// Combines this specification with another using OR logic.
    /// </summary>
    ISpecification<T> Or(ISpecification<T> other);

    /// <summary>
    /// Negates this specification.
    /// </summary>
    ISpecification<T> Not();
}
